from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
import os
import io
import csv
from datetime import datetime, date
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
import database as db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key_vintage_watches_2026")

# Configure Uploads
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'watches')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

DEFAULT_WATCH_IMAGES = {
    1: 'rolex_submariner_116610ln.jpg',
    2: 'omega_seamaster_21030422001001.jpg',
    3: 'seiko_presage_srpb43j1.jpg',
    4: 'tissot_prx_t1374071105100.jpg',
    5: 'citizen_ca0690_88e.jpg',
    6: 'casio_gg1000_1a3.jpg',
    7: 'orient_fac08003a0.jpg',
    8: 'longines_l37814566.jpg',
    9: 'hamilton_h70455553.jpg',
    10: 'tag_heuer_war211a_fc6180.jpg'
}

def attach_watch_image(w):
    if isinstance(w, dict):
        if not w.get('image'):
            w['image'] = DEFAULT_WATCH_IMAGES.get(w.get('watch_id'))
    return w

# ==========================================
# AUTHENTICATION HELPERS
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access the management portal.", "info")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access the management portal.", "info")
            return redirect(url_for('login'))
        if session.get('role') != 'Administrator':
            flash("Administrator privileges required for this action.", "error")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for customer cart count and template globals
@app.context_processor
def inject_cart_info():
    cart = session.get('cart', {})
    cart_count = sum(cart.values()) if isinstance(cart, dict) else 0
    return dict(cart_count=cart_count, date=date, today_date=str(date.today()))

# Helper to fetch active cart items with live database stock verification
def get_cart_details():
    cart = session.get('cart', {})
    items = []
    total = 0
    total_qty = 0
    cart_modified = False

    for watch_id_str, qty in list(cart.items()):
        try:
            watch_id = int(watch_id_str)
        except ValueError:
            cart.pop(watch_id_str, None)
            cart_modified = True
            continue

        watch = db.fetch_one("""
            SELECT w.*, COALESCE(SUM(i.quantity), 0) as stock 
            FROM watches w 
            LEFT JOIN inventory i ON w.watch_id = i.watch_id AND i.inventory_status != 'Out of Stock'
            WHERE w.watch_id = %s 
            GROUP BY w.watch_id
        """, (watch_id,))

        if watch:
            watch = attach_watch_image(watch)
            available_stock = int(watch['stock'])
            if available_stock <= 0:
                cart.pop(watch_id_str, None)
                cart_modified = True
                continue
            
            if qty > available_stock:
                qty = available_stock
                cart[watch_id_str] = qty
                cart_modified = True

            subtotal = float(watch['selling_price']) * qty
            total += subtotal
            total_qty += qty
            items.append({
                'watch': watch,
                'quantity': qty,
                'subtotal': subtotal,
                'stock': available_stock
            })
        else:
            cart.pop(watch_id_str, None)
            cart_modified = True

    if cart_modified:
        session['cart'] = cart
        session.modified = True

    return items, total, total_qty

# ==========================================
# PUBLIC CUSTOMER STOREFRONT ROUTES
# ==========================================
@app.route('/')
def index():
    featured_watches = db.fetch_all("""
        SELECT w.*, COALESCE(SUM(i.quantity), 0) as stock 
        FROM watches w
        LEFT JOIN inventory i ON w.watch_id = i.watch_id AND i.inventory_status = 'In Stock'
        WHERE w.status = 'Available'
        GROUP BY w.watch_id
        ORDER BY w.watch_id ASC
        LIMIT 6
    """)
    for w in featured_watches:
        attach_watch_image(w)
    brands = db.fetch_all("SELECT DISTINCT brand FROM watches ORDER BY brand")
    return render_template('store/home.html', featured_watches=featured_watches, brands=brands)

@app.route('/shop')
def shop_catalog():
    search = request.args.get('search', '').strip()
    brand = request.args.get('brand', '').strip()
    movement = request.args.get('movement', '').strip()
    sort = request.args.get('sort', 'newest')

    query = """
        SELECT w.*, COALESCE(SUM(i.quantity), 0) as stock 
        FROM watches w
        LEFT JOIN inventory i ON w.watch_id = i.watch_id AND i.inventory_status = 'In Stock'
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (w.model LIKE %s OR w.reference_number LIKE %s OR w.brand LIKE %s OR w.watch_type LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
    if brand:
        query += " AND w.brand = %s"
        params.append(brand)
    if movement:
        query += " AND w.movement = %s"
        params.append(movement)

    query += " GROUP BY w.watch_id"

    if sort == 'price_asc':
        query += " ORDER BY w.selling_price ASC"
    elif sort == 'price_desc':
        query += " ORDER BY w.selling_price DESC"
    else:
        query += " ORDER BY w.watch_id DESC"

    watches_list = db.fetch_all(query, tuple(params))
    for w in watches_list:
        attach_watch_image(w)
    all_brands = db.fetch_all("SELECT DISTINCT brand FROM watches ORDER BY brand")
    all_movements = db.fetch_all("SELECT DISTINCT movement FROM watches WHERE movement IS NOT NULL AND movement != '' ORDER BY movement")

    return render_template('store/catalog.html', 
                           watches=watches_list, 
                           search=search, 
                           selected_brand=brand, 
                           selected_movement=movement, 
                           selected_sort=sort,
                           brands=all_brands, 
                           movements=all_movements)

@app.route('/shop/watch/<int:watch_id>')
def watch_detail(watch_id):
    watch = db.fetch_one("""
        SELECT w.*, COALESCE(SUM(i.quantity), 0) as stock, 
               MAX(i.location) as sample_location
        FROM watches w
        LEFT JOIN inventory i ON w.watch_id = i.watch_id AND i.inventory_status = 'In Stock'
        WHERE w.watch_id = %s
        GROUP BY w.watch_id
    """, (watch_id,))

    if not watch:
        flash("The requested timepiece could not be found.", "error")
        return redirect(url_for('shop_catalog'))

    watch = attach_watch_image(watch)
    related_watches = db.fetch_all("""
        SELECT w.*, COALESCE(SUM(i.quantity), 0) as stock 
        FROM watches w
        LEFT JOIN inventory i ON w.watch_id = i.watch_id AND i.inventory_status = 'In Stock'
        WHERE w.brand = %s AND w.watch_id != %s AND w.status = 'Available'
        GROUP BY w.watch_id
        LIMIT 3
    """, (watch['brand'], watch_id))
    for rw in related_watches:
        attach_watch_image(rw)

    return render_template('store/watch_detail.html', watch=watch, related_watches=related_watches)

# ==========================================
# SHOPPING CART & CHECKOUT
# ==========================================
@app.route('/cart')
def view_cart():
    items, total, total_qty = get_cart_details()
    return render_template('store/cart.html', items=items, total=total, total_qty=total_qty)

@app.route('/cart/add/<int:watch_id>', methods=['POST'])
def cart_add(watch_id):
    qty = int(request.form.get('quantity', 1))
    if qty < 1:
        qty = 1

    stock_info = db.fetch_one("""
        SELECT COALESCE(SUM(quantity), 0) as stock 
        FROM inventory 
        WHERE watch_id = %s AND inventory_status = 'In Stock'
    """, (watch_id,))
    available_stock = int(stock_info['stock']) if stock_info else 0

    if available_stock <= 0:
        flash("This timepiece is currently out of stock.", "error")
        return redirect(request.referrer or url_for('shop_catalog'))

    if 'cart' not in session:
        session['cart'] = {}

    current_in_cart = session['cart'].get(str(watch_id), 0)
    new_qty = current_in_cart + qty

    if new_qty > available_stock:
        new_qty = available_stock
        flash(f"Only {available_stock} item(s) available in stock. Cart quantity adjusted to maximum.", "warning")
    else:
        flash("Timepiece added to your shopping cart.", "success")

    session['cart'][str(watch_id)] = new_qty
    session.modified = True

    if request.form.get('buy_now') == '1':
        return redirect(url_for('checkout'))

    return redirect(request.referrer or url_for('view_cart'))

@app.route('/cart/update/<int:watch_id>', methods=['POST'])
def cart_update(watch_id):
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})

    stock_info = db.fetch_one("""
        SELECT COALESCE(SUM(quantity), 0) as stock 
        FROM inventory 
        WHERE watch_id = %s AND inventory_status = 'In Stock'
    """, (watch_id,))
    available_stock = int(stock_info['stock']) if stock_info else 0

    if qty <= 0:
        cart.pop(str(watch_id), None)
        flash("Item removed from cart.", "info")
    elif qty > available_stock:
        cart[str(watch_id)] = available_stock
        flash(f"Maximum available stock for this timepiece is {available_stock}.", "warning")
    else:
        cart[str(watch_id)] = qty

    session['cart'] = cart
    session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:watch_id>', methods=['POST'])
def cart_remove(watch_id):
    cart = session.get('cart', {})
    cart.pop(str(watch_id), None)
    session['cart'] = cart
    session.modified = True
    flash("Item removed from cart.", "info")
    return redirect(url_for('view_cart'))

@app.route('/cart/clear', methods=['POST'])
def cart_clear():
    session.pop('cart', None)
    flash("Your shopping cart has been cleared.", "info")
    return redirect(url_for('view_cart'))

@app.route('/checkout')
def checkout():
    items, total, total_qty = get_cart_details()
    if not items:
        flash("Your shopping cart is empty.", "info")
        return redirect(url_for('shop_catalog'))
    return render_template('store/checkout.html', items=items, total=total, total_qty=total_qty)

@app.route('/checkout/process', methods=['POST'])
def checkout_process():
    items, total, total_qty = get_cart_details()
    if not items:
        flash("Your cart is empty. Please select watches to purchase.", "error")
        return redirect(url_for('shop_catalog'))

    full_name = request.form.get('full_name', '').strip()
    contact_number = request.form.get('contact_number', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    payment_method = request.form.get('payment_method', 'Cash')

    if not full_name or not contact_number or not email or not address:
        flash("Please complete all required customer information.", "error")
        return redirect(url_for('checkout'))

    def do_checkout_transaction(cursor):
        for item in items:
            w_id = item['watch']['watch_id']
            needed_qty = item['quantity']
            cursor.execute("""
                SELECT COALESCE(SUM(quantity), 0) as current_stock 
                FROM inventory 
                WHERE watch_id = %s AND inventory_status = 'In Stock'
                FOR UPDATE
            """, (w_id,))
            row = cursor.fetchone()
            curr_stock = int(row['current_stock']) if row else 0
            if curr_stock < needed_qty:
                raise ValueError(f"Insufficient stock for {item['watch']['brand']} {item['watch']['model']}.")

        cursor.execute("SELECT customer_id FROM customer WHERE email = %s LIMIT 1", (email,))
        existing_cust = cursor.fetchone()
        if existing_cust:
            customer_id = existing_cust['customer_id']
            cursor.execute("""
                UPDATE customer 
                SET full_name = %s, contact_number = %s, address = %s 
                WHERE customer_id = %s
            """, (full_name, contact_number, address, customer_id))
        else:
            cursor.execute("""
                INSERT INTO customer (full_name, contact_number, email, address, customer_type, date_registered)
                VALUES (%s, %s, %s, %s, 'Regular', CURDATE())
            """, (full_name, contact_number, email, address))
            customer_id = cursor.lastrowid

        cashier_user_id = 1
        cursor.execute("""
            INSERT INTO sales (customer_id, user_id, sale_date, total_amount, paymaent_method, payment_status)
            VALUES (%s, %s, CURDATE(), %s, %s, 'Paid')
        """, (customer_id, cashier_user_id, total, payment_method))
        sale_id = cursor.lastrowid

        for item in items:
            w_id = item['watch']['watch_id']
            qty = item['quantity']
            unit_price = float(item['watch']['selling_price'])
            subtotal = unit_price * qty

            cursor.execute("""
                INSERT INTO `sale items` (sale_id, watch_id, quantity, unit_price, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (sale_id, w_id, qty, unit_price, subtotal))

            cursor.execute("""
                SELECT inventory_id, quantity 
                FROM inventory 
                WHERE watch_id = %s AND quantity > 0 
                ORDER BY date_added ASC 
                FOR UPDATE
            """, (w_id,))
            inv_rows = cursor.fetchall()
            
            remaining_to_deduct = qty
            for inv in inv_rows:
                if remaining_to_deduct <= 0:
                    break
                inv_id = inv['inventory_id']
                inv_qty = inv['quantity']
                
                if inv_qty <= remaining_to_deduct:
                    remaining_to_deduct -= inv_qty
                    new_inv_qty = 0
                    new_status = 'Out of Stock'
                else:
                    new_inv_qty = inv_qty - remaining_to_deduct
                    remaining_to_deduct = 0
                    new_status = 'In Stock'

                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = %s, inventory_status = %s 
                    WHERE inventory_id = %s
                """, (new_inv_qty, new_status, inv_id))

            cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total_rem FROM inventory WHERE watch_id = %s", (w_id,))
            rem_row = cursor.fetchone()
            total_remaining = int(rem_row['total_rem']) if rem_row else 0
            if total_remaining <= 0:
                cursor.execute("UPDATE watches SET status = 'Sold Out' WHERE watch_id = %s", (w_id,))

        return sale_id

    sale_id = db.execute_transaction(do_checkout_transaction)

    if sale_id:
        session.pop('cart', None)
        flash("Order completed successfully! Thank you for your purchase.", "success")
        return redirect(url_for('order_confirmation', sale_id=sale_id))
    else:
        flash("Failed to process transaction. Please verify stock availability and try again.", "error")
        return redirect(url_for('checkout'))

@app.route('/order/confirmation/<int:sale_id>')
def order_confirmation(sale_id):
    sale = db.fetch_one("""
        SELECT s.*, c.full_name as customer_name, c.email as customer_email, 
               c.contact_number as customer_phone, c.address as customer_address,
               u.full_name as cashier_name
        FROM sales s
        JOIN customer c ON s.customer_id = c.customer_id
        LEFT JOIN user u ON s.user_id = u.user_id
        WHERE s.sale_id = %s
    """, (sale_id,))

    if not sale:
        flash("Order record not found.", "error")
        return redirect(url_for('shop_catalog'))

    items = db.fetch_all("""
        SELECT si.*, w.brand, w.model, w.reference_number 
        FROM `sale items` si
        JOIN watches w ON si.watch_id = w.watch_id
        WHERE si.sale_id = %s
    """, (sale_id,))

    return render_template('store/order_success.html', sale=sale, items=items)

# ==========================================
# AUTHENTICATION (STAFF & ADMIN)
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = db.fetch_one("SELECT * FROM user WHERE user_name = %s AND status = 'Active'", (username,))
        
        if user:
            match = False
            user_pwd = str(user['password'])
            if user_pwd.startswith('pbkdf2:sha256:') or user_pwd.startswith('scrypt:'):
                match = check_password_hash(user_pwd, password)
            else:
                match = (user_pwd == password)
                
            if match:
                session['user_id'] = user['user_id']
                session['full_name'] = user['full_name']
                session['role'] = user['role']
                flash(f"Welcome back, {user['full_name']}!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid username or password.", "error")
        else:
            flash("Invalid credentials or inactive account.", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))

# ==========================================
# ADMIN DASHBOARD
# ==========================================
@app.route('/dashboard')
@login_required
def dashboard():
    total_watches = db.fetch_one("SELECT COUNT(*) as count FROM watches")['count']
    available_inventory = db.fetch_one("SELECT COALESCE(SUM(quantity), 0) as total FROM inventory WHERE inventory_status = 'In Stock'")['total']
    low_stock_count = db.fetch_one("SELECT COUNT(*) as count FROM inventory WHERE quantity > 0 AND quantity <= 2")['count']
    total_customers = db.fetch_one("SELECT COUNT(*) as count FROM customer")['count']
    sales_today = db.fetch_one("SELECT COALESCE(SUM(total_amount), 0) as total FROM sales WHERE sale_date = CURDATE()")['total']
    monthly_revenue = db.fetch_one("SELECT COALESCE(SUM(total_amount), 0) as total FROM sales WHERE MONTH(sale_date) = MONTH(CURDATE()) AND YEAR(sale_date) = YEAR(CURDATE())")['total']
    active_services = db.fetch_one("SELECT COUNT(*) as count FROM watch_services WHERE service_status IN ('Pending', 'In Progress')")['count']
    active_investors = db.fetch_one("SELECT COUNT(*) as count FROM investors WHERE investment_status = 'Active'")['count']

    recent_sales = db.fetch_all("""
        SELECT s.sale_id, c.full_name as customer, u.full_name as staff, s.sale_date, s.total_amount, s.payment_status
        FROM sales s
        JOIN customer c ON s.customer_id = c.customer_id
        LEFT JOIN user u ON s.user_id = u.user_id
        ORDER BY s.sale_date DESC, s.sale_id DESC LIMIT 5
    """)
    
    recent_watches = db.fetch_all("""
        SELECT w.watch_id, w.brand, w.model, w.selling_price, w.condition_status, w.status,
               COALESCE(SUM(i.quantity), 0) as stock
        FROM watches w
        LEFT JOIN inventory i ON w.watch_id = i.watch_id
        GROUP BY w.watch_id
        ORDER BY w.watch_id DESC LIMIT 5
    """)

    low_stock_items = db.fetch_all("""
        SELECT i.inventory_id, w.brand, w.model, i.quantity, i.location, i.inventory_status
        FROM inventory i
        JOIN watches w ON i.watch_id = w.watch_id
        WHERE i.quantity <= 2
        ORDER BY i.quantity ASC LIMIT 5
    """)

    return render_template('dashboard.html', 
                           total_watches=total_watches, 
                           available_inventory=available_inventory, 
                           low_stock_count=low_stock_count,
                           total_customers=total_customers, 
                           sales_today=sales_today,
                           monthly_revenue=monthly_revenue,
                           active_services=active_services,
                           active_investors=active_investors,
                           recent_sales=recent_sales,
                           recent_watches=recent_watches,
                           low_stock_items=low_stock_items)

# ==========================================
# WATCHES CATALOG (ADMIN CRUD)
# ==========================================
@app.route('/watches')
@login_required
def watches():
    search = request.args.get('search', '').strip()
    brand = request.args.get('brand', '').strip()
    
    query = """
        SELECT w.*, COALESCE(SUM(i.quantity), 0) as total_stock 
        FROM watches w
        LEFT JOIN inventory i ON w.watch_id = i.watch_id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (w.model LIKE %s OR w.reference_number LIKE %s OR w.brand LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if brand:
        query += " AND w.brand = %s"
        params.append(brand)
        
    query += " GROUP BY w.watch_id ORDER BY w.watch_id DESC"
    watches_list = db.fetch_all(query, tuple(params))
    for w in watches_list:
        attach_watch_image(w)
    brands = db.fetch_all("SELECT DISTINCT brand FROM watches ORDER BY brand")
    
    return render_template('watches.html', watches=watches_list, search=search, brand=brand, brands=brands)

@app.route('/watches/add', methods=['POST'])
@login_required
def watch_add():
    brand = request.form.get('brand', '').strip()
    model = request.form.get('model', '').strip()
    reference_number = request.form.get('reference_number', '').strip()
    watch_type = request.form.get('watch_type', '').strip()
    movement = request.form.get('movement', '').strip()
    condition_status = request.form.get('condition_status', 'Very Good')
    purchase_price = float(request.form.get('purchase_price', 0))
    selling_price = float(request.form.get('selling_price', 0))
    year_aquired = request.form.get('year_aquired', str(datetime.now().year))
    status = request.form.get('status', 'Available')
    description = request.form.get('description', '').strip()
    initial_stock = int(request.form.get('initial_stock', 1))
    stock_location = request.form.get('stock_location', 'Display Cabinet A').strip()

    if not brand or not model or not reference_number:
        flash("Brand, Model, and Reference Number are required.", "error")
        return redirect(url_for('watches'))

    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            safe_name = f"{secure_filename(brand)}_{secure_filename(model)}_{int(datetime.now().timestamp())}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], safe_name))
            image_filename = safe_name

    query = """
        INSERT INTO watches (brand, model, reference_number, watch_type, movement, 
                             condition_status, purchase_price, selling_price, year_aquired, status, image, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    watch_id = db.execute_query(query, (brand, model, reference_number, watch_type, movement,
                                        condition_status, purchase_price, selling_price, year_aquired, 
                                        status, image_filename, description))

    if watch_id:
        inv_status = 'In Stock' if initial_stock > 0 else 'Out of Stock'
        db.execute_query("""
            INSERT INTO inventory (watch_id, quantity, location, date_added, inventory_status)
            VALUES (%s, %s, %s, CURDATE(), %s)
        """, (watch_id, initial_stock, stock_location, inv_status))

        flash(f"Timepiece '{brand} {model}' added to catalog with {initial_stock} in stock.", "success")
    else:
        flash("Failed to add watch. Please verify all details.", "error")

    return redirect(url_for('watches'))

@app.route('/watches/edit/<int:watch_id>', methods=['POST'])
@login_required
def watch_edit(watch_id):
    brand = request.form.get('brand', '').strip()
    model = request.form.get('model', '').strip()
    reference_number = request.form.get('reference_number', '').strip()
    watch_type = request.form.get('watch_type', '').strip()
    movement = request.form.get('movement', '').strip()
    condition_status = request.form.get('condition_status', '').strip()
    purchase_price = float(request.form.get('purchase_price', 0))
    selling_price = float(request.form.get('selling_price', 0))
    year_aquired = request.form.get('year_aquired', '').strip()
    status = request.form.get('status', 'Available')
    description = request.form.get('description', '').strip()

    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            safe_name = f"{secure_filename(brand)}_{secure_filename(model)}_{int(datetime.now().timestamp())}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], safe_name))
            image_filename = safe_name

    if image_filename:
        query = """
            UPDATE watches 
            SET brand=%s, model=%s, reference_number=%s, watch_type=%s, movement=%s,
                condition_status=%s, purchase_price=%s, selling_price=%s, year_aquired=%s, 
                status=%s, image=%s, description=%s
            WHERE watch_id=%s
        """
        params = (brand, model, reference_number, watch_type, movement, condition_status,
                  purchase_price, selling_price, year_aquired, status, image_filename, description, watch_id)
    else:
        query = """
            UPDATE watches 
            SET brand=%s, model=%s, reference_number=%s, watch_type=%s, movement=%s,
                condition_status=%s, purchase_price=%s, selling_price=%s, year_aquired=%s, 
                status=%s, description=%s
            WHERE watch_id=%s
        """
        params = (brand, model, reference_number, watch_type, movement, condition_status,
                  purchase_price, selling_price, year_aquired, status, description, watch_id)

    success = db.execute_query(query, params)
    if success:
        flash(f"Timepiece '{brand} {model}' updated successfully.", "success")
    else:
        flash("Failed to update timepiece record.", "error")

    return redirect(url_for('watches'))

@app.route('/watches/delete/<int:watch_id>', methods=['POST'])
@login_required
def watch_delete(watch_id):
    sale_count = db.fetch_one("SELECT COUNT(*) as c FROM `sale items` WHERE watch_id = %s", (watch_id,))['c']
    service_count = db.fetch_one("SELECT COUNT(*) as c FROM watch_services WHERE watch_id = %s", (watch_id,))['c']

    if sale_count > 0 or service_count > 0:
        db.execute_query("UPDATE watches SET status = 'Discontinued' WHERE watch_id = %s", (watch_id,))
        db.execute_query("UPDATE inventory SET inventory_status = 'Out of Stock', quantity = 0 WHERE watch_id = %s", (watch_id,))
        flash("Watch cannot be hard-deleted as it is linked to existing transactions or services. It has been marked as 'Discontinued' and stock set to 0.", "warning")
    else:
        db.execute_query("DELETE FROM inventory WHERE watch_id = %s", (watch_id,))
        db.execute_query("DELETE FROM watches WHERE watch_id = %s", (watch_id,))
        flash("Watch and its inventory records deleted successfully.", "success")

    return redirect(url_for('watches'))

@app.route('/api/watch/<int:watch_id>')
def get_watch_api(watch_id):
    watch = db.fetch_one("""
        SELECT w.*, COALESCE(SUM(i.quantity), 0) as current_stock,
               MAX(i.location) as sample_location, MAX(i.inventory_id) as inv_id
        FROM watches w
        LEFT JOIN inventory i ON w.watch_id = i.watch_id
        WHERE w.watch_id = %s
        GROUP BY w.watch_id
    """, (watch_id,))
    if watch:
        watch['purchase_price_formatted'] = f"₱ {float(watch['purchase_price']):,.2f}"
        watch['selling_price_formatted'] = f"₱ {float(watch['selling_price']):,.2f}"
        return jsonify(watch)
    return jsonify({"error": "Watch not found"}), 404

# ==========================================
# INVENTORY MANAGEMENT (ADMIN CRUD)
# ==========================================
@app.route('/inventory')
@login_required
def inventory():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    query = """
        SELECT i.inventory_id, w.watch_id, w.brand, w.model, w.reference_number, 
               i.quantity, i.location, i.date_added, i.inventory_status
        FROM inventory i
        JOIN watches w ON i.watch_id = w.watch_id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (w.brand LIKE %s OR w.model LIKE %s OR i.location LIKE %s OR w.reference_number LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
    if status_filter:
        query += " AND i.inventory_status = %s"
        params.append(status_filter)
        
    query += " ORDER BY i.inventory_id DESC"
    inventory_items = db.fetch_all(query, tuple(params))
    all_watches = db.fetch_all("SELECT watch_id, brand, model, reference_number FROM watches ORDER BY brand, model")
    
    return render_template('inventory.html', inventory=inventory_items, search=search, status_filter=status_filter, watches=all_watches)

@app.route('/inventory/add', methods=['POST'])
@login_required
def inventory_add():
    watch_id = request.form.get('watch_id')
    quantity = int(request.form.get('quantity', 1))
    location = request.form.get('location', 'Display Cabinet A').strip()
    status = 'In Stock' if quantity > 0 else 'Out of Stock'

    if not watch_id or quantity < 0:
        flash("Valid timepiece and non-negative quantity required.", "error")
        return redirect(url_for('inventory'))

    query = """
        INSERT INTO inventory (watch_id, quantity, location, date_added, inventory_status)
        VALUES (%s, %s, %s, CURDATE(), %s)
    """
    res = db.execute_query(query, (watch_id, quantity, location, status))
    if res:
        db.execute_query("UPDATE watches SET status = 'Available' WHERE watch_id = %s", (watch_id,))
        flash("Stock record added successfully.", "success")
    else:
        flash("Failed to add inventory record.", "error")

    return redirect(url_for('inventory'))

@app.route('/inventory/edit/<int:inventory_id>', methods=['POST'])
@login_required
def inventory_edit(inventory_id):
    quantity = int(request.form.get('quantity', 0))
    location = request.form.get('location', '').strip()
    status = request.form.get('inventory_status')

    if quantity <= 0:
        status = 'Out of Stock'
        quantity = 0
    elif not status:
        status = 'In Stock'

    query = "UPDATE inventory SET quantity = %s, location = %s, inventory_status = %s WHERE inventory_id = %s"
    res = db.execute_query(query, (quantity, location, status, inventory_id))

    if res:
        inv = db.fetch_one("SELECT watch_id FROM inventory WHERE inventory_id = %s", (inventory_id,))
        if inv:
            w_id = inv['watch_id']
            tot = db.fetch_one("SELECT COALESCE(SUM(quantity), 0) as s FROM inventory WHERE watch_id = %s", (w_id,))['s']
            w_status = 'Available' if tot > 0 else 'Sold Out'
            db.execute_query("UPDATE watches SET status = %s WHERE watch_id = %s", (w_status, w_id))

        flash("Inventory record updated successfully.", "success")
    else:
        flash("Failed to update inventory record.", "error")

    return redirect(url_for('inventory'))

@app.route('/inventory/delete/<int:inventory_id>', methods=['POST'])
@login_required
def inventory_delete(inventory_id):
    db.execute_query("DELETE FROM inventory WHERE inventory_id = %s", (inventory_id,))
    flash("Inventory entry removed.", "info")
    return redirect(url_for('inventory'))

@app.route('/api/inventory/<int:inventory_id>')
@login_required
def get_inventory_api(inventory_id):
    inv = db.fetch_one("""
        SELECT i.*, w.brand, w.model, w.reference_number 
        FROM inventory i 
        JOIN watches w ON i.watch_id = w.watch_id 
        WHERE i.inventory_id = %s
    """, (inventory_id,))
    if inv:
        return jsonify(inv)
    return jsonify({"error": "Inventory record not found"}), 404

# ==========================================
# CUSTOMER MANAGEMENT (ADMIN CRUD)
# ==========================================
@app.route('/customers')
@login_required
def customers():
    search = request.args.get('search', '').strip()
    query = """
        SELECT c.*, 
               COUNT(DISTINCT s.sale_id) as total_orders, 
               COALESCE(SUM(s.total_amount), 0) as total_spent
        FROM customer c
        LEFT JOIN sales s ON c.customer_id = s.customer_id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (c.full_name LIKE %s OR c.email LIKE %s OR c.contact_number LIKE %s OR c.address LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
        
    query += " GROUP BY c.customer_id ORDER BY c.customer_id DESC"
    customer_list = db.fetch_all(query, tuple(params))
    return render_template('customers.html', customers=customer_list, search=search)

@app.route('/customers/add', methods=['POST'])
@login_required
def customer_add():
    full_name = request.form.get('full_name', '').strip()
    contact_number = request.form.get('contact_number', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    customer_type = request.form.get('customer_type', 'Regular')

    if not full_name or not contact_number or not email:
        flash("Full Name, Contact Number, and Email are required.", "error")
        return redirect(url_for('customers'))

    query = """
        INSERT INTO customer (full_name, contact_number, email, address, customer_type, date_registered)
        VALUES (%s, %s, %s, %s, %s, CURDATE())
    """
    res = db.execute_query(query, (full_name, contact_number, email, address, customer_type))
    if res:
        flash(f"Customer '{full_name}' created successfully.", "success")
    else:
        flash("Failed to add customer. Email may already be registered.", "error")

    return redirect(url_for('customers'))

@app.route('/customers/edit/<int:customer_id>', methods=['POST'])
@login_required
def customer_edit(customer_id):
    full_name = request.form.get('full_name', '').strip()
    contact_number = request.form.get('contact_number', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    customer_type = request.form.get('customer_type', 'Regular')

    query = """
        UPDATE customer 
        SET full_name = %s, contact_number = %s, email = %s, address = %s, customer_type = %s
        WHERE customer_id = %s
    """
    res = db.execute_query(query, (full_name, contact_number, email, address, customer_type, customer_id))
    if res:
        flash("Customer details updated successfully.", "success")
    else:
        flash("Failed to update customer record.", "error")

    return redirect(url_for('customers'))

@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
def customer_delete(customer_id):
    has_sales = db.fetch_one("SELECT COUNT(*) as c FROM sales WHERE customer_id = %s", (customer_id,))['c']
    has_services = db.fetch_one("SELECT COUNT(*) as c FROM watch_services WHERE customer_id = %s", (customer_id,))['c']

    if has_sales > 0 or has_services > 0:
        flash("Customer cannot be deleted because they have associated sales transactions or service orders.", "error")
    else:
        db.execute_query("DELETE FROM customer WHERE customer_id = %s", (customer_id,))
        flash("Customer record deleted successfully.", "success")

    return redirect(url_for('customers'))

@app.route('/api/customer/<int:customer_id>')
@login_required
def get_customer_api(customer_id):
    customer = db.fetch_one("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    orders = db.fetch_all("""
        SELECT sale_id, sale_date, total_amount, paymaent_method, payment_status 
        FROM sales 
        WHERE customer_id = %s 
        ORDER BY sale_date DESC
    """, (customer_id,))

    services = db.fetch_all("""
        SELECT ws.service_id, ws.service_type, ws.service_date, ws.service_cost, ws.service_status,
               w.brand, w.model 
        FROM watch_services ws
        LEFT JOIN watches w ON ws.watch_id = w.watch_id
        WHERE ws.customer_id = %s
        ORDER BY ws.service_date DESC
    """, (customer_id,))

    customer['orders'] = orders
    customer['services'] = services
    return jsonify(customer)

# ==========================================
# WATCH SERVICES MODULE (ADMIN CRUD)
# ==========================================
@app.route('/services')
@login_required
def services():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    service_type = request.args.get('service_type', '').strip()

    query = """
        SELECT ws.*, w.brand, w.model, w.reference_number, 
               c.full_name as customer_name, c.contact_number as customer_phone
        FROM watch_services ws
        LEFT JOIN watches w ON ws.watch_id = w.watch_id
        LEFT JOIN customer c ON ws.customer_id = c.customer_id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (c.full_name LIKE %s OR w.brand LIKE %s OR w.model LIKE %s OR ws.service_description LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
    if status_filter:
        query += " AND ws.service_status = %s"
        params.append(status_filter)
    if service_type:
        query += " AND ws.service_type = %s"
        params.append(service_type)

    query += " ORDER BY ws.service_date DESC, ws.service_id DESC"
    service_items = db.fetch_all(query, tuple(params))

    watches = db.fetch_all("SELECT watch_id, brand, model, reference_number FROM watches ORDER BY brand, model")
    customers = db.fetch_all("SELECT customer_id, full_name, contact_number FROM customer ORDER BY full_name")

    total_services = len(service_items)
    pending_services = sum(1 for s in service_items if s['service_status'] in ['Pending', 'In Progress'])
    total_service_revenue = sum(float(s['service_cost']) for s in service_items if s['service_status'] == 'Completed')

    return render_template('services.html', 
                           services=service_items, 
                           watches=watches, 
                           customers=customers, 
                           search=search, 
                           status_filter=status_filter, 
                           service_type=service_type,
                           total_services=total_services,
                           pending_services=pending_services,
                           total_service_revenue=total_service_revenue)

@app.route('/services/add', methods=['POST'])
@login_required
def service_add():
    watch_id = request.form.get('watch_id')
    customer_id = request.form.get('customer_id')
    service_type = request.form.get('service_type', 'Maintenance')
    service_description = request.form.get('service_description', '').strip()
    service_date = request.form.get('service_date', str(date.today()))
    service_cost = float(request.form.get('service_cost', 0))
    service_status = request.form.get('service_status', 'Pending')

    if not watch_id or not customer_id or not service_description:
        flash("Timepiece, Customer, and Description are required.", "error")
        return redirect(url_for('services'))

    query = """
        INSERT INTO watch_services (watch_id, customer_id, service_type, service_description, service_date, service_cost, service_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    res = db.execute_query(query, (watch_id, customer_id, service_type, service_description, service_date, service_cost, service_status))
    if res:
        flash("Service order logged successfully.", "success")
    else:
        flash("Failed to log service order.", "error")

    return redirect(url_for('services'))

@app.route('/services/edit/<int:service_id>', methods=['POST'])
@login_required
def service_edit(service_id):
    service_type = request.form.get('service_type')
    service_description = request.form.get('service_description', '').strip()
    service_date = request.form.get('service_date')
    service_cost = float(request.form.get('service_cost', 0))
    service_status = request.form.get('service_status')

    query = """
        UPDATE watch_services 
        SET service_type = %s, service_description = %s, service_date = %s, service_cost = %s, service_status = %s
        WHERE service_id = %s
    """
    res = db.execute_query(query, (service_type, service_description, service_date, service_cost, service_status, service_id))
    if res:
        flash("Service order updated successfully.", "success")
    else:
        flash("Failed to update service order.", "error")

    return redirect(url_for('services'))

@app.route('/services/status/<int:service_id>', methods=['POST'])
@login_required
def service_status_quick(service_id):
    new_status = request.form.get('service_status')
    if new_status:
        db.execute_query("UPDATE watch_services SET service_status = %s WHERE service_id = %s", (new_status, service_id))
        flash(f"Service status updated to {new_status}.", "success")
    return redirect(url_for('services'))

@app.route('/services/delete/<int:service_id>', methods=['POST'])
@login_required
def service_delete(service_id):
    db.execute_query("DELETE FROM watch_services WHERE service_id = %s", (service_id,))
    flash("Service record deleted.", "info")
    return redirect(url_for('services'))

@app.route('/api/service/<int:service_id>')
@login_required
def get_service_api(service_id):
    service = db.fetch_one("""
        SELECT ws.*, w.brand, w.model, c.full_name as customer_name
        FROM watch_services ws
        LEFT JOIN watches w ON ws.watch_id = w.watch_id
        LEFT JOIN customer c ON ws.customer_id = c.customer_id
        WHERE ws.service_id = %s
    """, (service_id,))
    if service:
        service['service_cost'] = float(service['service_cost'])
        return jsonify(service)
    return jsonify({"error": "Service not found"}), 404

# ==========================================
# INVESTORS MODULE (ADMIN CRUD)
# ==========================================
@app.route('/investors')
@login_required
def investors():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = "SELECT * FROM investors WHERE 1=1"
    params = []

    if search:
        query += " AND (investor_name LIKE %s OR contact_number LIKE %s OR email LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if status_filter:
        query += " AND investment_status = %s"
        params.append(status_filter)

    query += " ORDER BY investment_date DESC, investor_id DESC"
    investor_list = db.fetch_all(query, tuple(params))

    total_capital = sum(float(i['investment_amount']) for i in investor_list)
    active_count = sum(1 for i in investor_list if i['investment_status'] == 'Active')
    avg_investment = (total_capital / len(investor_list)) if investor_list else 0

    return render_template('investors.html', 
                           investors=investor_list, 
                           search=search, 
                           status_filter=status_filter,
                           total_capital=total_capital,
                           active_count=active_count,
                           avg_investment=avg_investment)

@app.route('/investors/add', methods=['POST'])
@login_required
def investor_add():
    investor_name = request.form.get('investor_name', '').strip()
    contact_number = request.form.get('contact_number', '').strip()
    email = request.form.get('email', '').strip()
    investment_amount = float(request.form.get('investment_amount', 0))
    investment_date = request.form.get('investment_date', str(date.today()))
    investment_status = request.form.get('investment_status', 'Active')

    if not investor_name or not contact_number or investment_amount <= 0:
        flash("Investor name, valid contact number, and investment amount are required.", "error")
        return redirect(url_for('investors'))

    query = """
        INSERT INTO investors (investor_name, contact_number, email, investment_amount, investment_date, investment_status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    res = db.execute_query(query, (investor_name, contact_number, email, investment_amount, investment_date, investment_status))
    if res:
        flash(f"Investor '{investor_name}' recorded successfully.", "success")
    else:
        flash("Failed to add investor record.", "error")

    return redirect(url_for('investors'))

@app.route('/investors/edit/<int:investor_id>', methods=['POST'])
@login_required
def investor_edit(investor_id):
    investor_name = request.form.get('investor_name', '').strip()
    contact_number = request.form.get('contact_number', '').strip()
    email = request.form.get('email', '').strip()
    investment_amount = float(request.form.get('investment_amount', 0))
    investment_date = request.form.get('investment_date')
    investment_status = request.form.get('investment_status')

    query = """
        UPDATE investors 
        SET investor_name = %s, contact_number = %s, email = %s, 
            investment_amount = %s, investment_date = %s, investment_status = %s
        WHERE investor_id = %s
    """
    res = db.execute_query(query, (investor_name, contact_number, email, investment_amount, investment_date, investment_status, investor_id))
    if res:
        flash("Investor record updated successfully.", "success")
    else:
        flash("Failed to update investor record.", "error")

    return redirect(url_for('investors'))

@app.route('/investors/delete/<int:investor_id>', methods=['POST'])
@login_required
def investor_delete(investor_id):
    db.execute_query("DELETE FROM investors WHERE investor_id = %s", (investor_id,))
    flash("Investor record removed.", "info")
    return redirect(url_for('investors'))

@app.route('/api/investor/<int:investor_id>')
@login_required
def get_investor_api(investor_id):
    inv = db.fetch_one("SELECT * FROM investors WHERE investor_id = %s", (investor_id,))
    if inv:
        inv['investment_amount'] = float(inv['investment_amount'])
        return jsonify(inv)
    return jsonify({"error": "Investor not found"}), 404

# ==========================================
# USER & STAFF MANAGEMENT (ADMIN ONLY)
# ==========================================
@app.route('/users')
@admin_required
def users():
    user_list = db.fetch_all("SELECT user_id, full_name, user_name, role, email, status FROM user ORDER BY user_id")
    return render_template('users.html', users=user_list)

@app.route('/users/add', methods=['POST'])
@admin_required
def user_add():
    full_name = request.form.get('full_name', '').strip()
    user_name = request.form.get('user_name', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'Sales Staff')
    email = request.form.get('email', '').strip()
    status = request.form.get('status', 'Active')

    if not full_name or not user_name or not password or not email:
        flash("All fields are required to register staff.", "error")
        return redirect(url_for('users'))

    exists = db.fetch_one("SELECT user_id FROM user WHERE user_name = %s", (user_name,))
    if exists:
        flash("That username is already in use.", "error")
        return redirect(url_for('users'))

    hashed_pw = generate_password_hash(password)
    query = """
        INSERT INTO user (full_name, user_name, password, role, email, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    res = db.execute_query(query, (full_name, user_name, hashed_pw, role, email, status))
    if res:
        flash(f"User account '{user_name}' created successfully.", "success")
    else:
        flash("Failed to create user account.", "error")

    return redirect(url_for('users'))

@app.route('/users/edit/<int:user_id>', methods=['POST'])
@admin_required
def user_edit(user_id):
    full_name = request.form.get('full_name', '').strip()
    role = request.form.get('role')
    email = request.form.get('email', '').strip()
    status = request.form.get('status')
    new_password = request.form.get('password', '').strip()

    if new_password:
        hashed_pw = generate_password_hash(new_password)
        query = "UPDATE user SET full_name = %s, role = %s, email = %s, status = %s, password = %s WHERE user_id = %s"
        params = (full_name, role, email, status, hashed_pw, user_id)
    else:
        query = "UPDATE user SET full_name = %s, role = %s, email = %s, status = %s WHERE user_id = %s"
        params = (full_name, role, email, status, user_id)

    res = db.execute_query(query, params)
    if res:
        flash("User details updated successfully.", "success")
    else:
        flash("Failed to update user.", "error")

    return redirect(url_for('users'))

@app.route('/users/toggle-status/<int:user_id>', methods=['POST'])
@admin_required
def user_toggle_status(user_id):
    if user_id == session.get('user_id'):
        flash("You cannot deactivate your own current active session.", "error")
        return redirect(url_for('users'))

    u = db.fetch_one("SELECT status FROM user WHERE user_id = %s", (user_id,))
    if u:
        new_status = 'Inactive' if u['status'] == 'Active' else 'Active'
        db.execute_query("UPDATE user SET status = %s WHERE user_id = %s", (new_status, user_id))
        flash(f"User status updated to {new_status}.", "success")

    return redirect(url_for('users'))

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def user_delete(user_id):
    if user_id == session.get('user_id'):
        flash("You cannot delete your own account.", "error")
        return redirect(url_for('users'))

    sales_count = db.fetch_one("SELECT COUNT(*) as c FROM sales WHERE user_id = %s", (user_id,))['c']
    if sales_count > 0:
        db.execute_query("UPDATE user SET status = 'Inactive' WHERE user_id = %s", (user_id,))
        flash("User has associated sales records and cannot be permanently removed. The account has been deactivated instead.", "warning")
    else:
        db.execute_query("DELETE FROM user WHERE user_id = %s", (user_id,))
        flash("User account deleted successfully.", "success")

    return redirect(url_for('users'))

@app.route('/api/user/<int:user_id>')
@admin_required
def get_user_api(user_id):
    u = db.fetch_one("SELECT user_id, full_name, user_name, role, email, status FROM user WHERE user_id = %s", (user_id,))
    if u:
        return jsonify(u)
    return jsonify({"error": "User not found"}), 404

# ==========================================
# SALES HISTORY & IN-STORE SALE (ADMIN)
# ==========================================
@app.route('/sales')
@login_required
def sales():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = """
        SELECT s.sale_id, c.full_name as customer, u.full_name as staff, 
               s.sale_date, s.total_amount, s.paymaent_method, s.payment_status
        FROM sales s
        JOIN customer c ON s.customer_id = c.customer_id
        LEFT JOIN user u ON s.user_id = u.user_id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (c.full_name LIKE %s OR s.paymaent_method LIKE %s OR u.full_name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if status_filter:
        query += " AND s.payment_status = %s"
        params.append(status_filter)
    if date_from:
        query += " AND s.sale_date >= %s"
        params.append(date_from)
    if date_to:
        query += " AND s.sale_date <= %s"
        params.append(date_to)

    query += " ORDER BY s.sale_date DESC, s.sale_id DESC"
    sales_list = db.fetch_all(query, tuple(params))
    
    customers = db.fetch_all("SELECT customer_id, full_name FROM customer ORDER BY full_name")
    available_watches = db.fetch_all("""
        SELECT w.watch_id, w.brand, w.model, w.selling_price, COALESCE(SUM(i.quantity), 0) as quantity 
        FROM watches w
        JOIN inventory i ON w.watch_id = i.watch_id
        WHERE i.quantity > 0 AND i.inventory_status = 'In Stock'
        GROUP BY w.watch_id
        ORDER BY w.brand, w.model
    """)
    
    total_sales_val = sum(float(s['total_amount']) for s in sales_list)
    paid_sales_val = sum(float(s['total_amount']) for s in sales_list if s['payment_status'] == 'Paid')

    return render_template('sales.html', 
                           sales=sales_list, 
                           customers=customers, 
                           available_watches=available_watches, 
                           search=search, 
                           status_filter=status_filter,
                           date_from=date_from,
                           date_to=date_to,
                           total_sales_val=total_sales_val,
                           paid_sales_val=paid_sales_val)

@app.route('/sales/new', methods=['POST'])
@login_required
def new_sale():
    customer_id = request.form.get('customer_id')
    watch_id = request.form.get('watch_id')
    quantity = int(request.form.get('quantity', 1))
    payment_method = request.form.get('payment_method', 'Cash')
    payment_status = request.form.get('payment_status', 'Paid')
    user_id = session['user_id']
    
    if not customer_id or not watch_id:
        flash("Customer and Watch selection are required.", "error")
        return redirect(url_for('sales'))

    def do_instore_sale(cursor):
        cursor.execute("SELECT selling_price, brand, model FROM watches WHERE watch_id = %s", (watch_id,))
        watch = cursor.fetchone()
        if not watch:
            raise ValueError("Watch record not found.")

        cursor.execute("""
            SELECT COALESCE(SUM(quantity), 0) as stock 
            FROM inventory 
            WHERE watch_id = %s AND inventory_status = 'In Stock'
            FOR UPDATE
        """, (watch_id,))
        curr_stock = int(cursor.fetchone()['stock'])
        if curr_stock < quantity:
            raise ValueError(f"Insufficient stock. Only {curr_stock} available.")

        total_amount = float(watch['selling_price']) * quantity

        cursor.execute("""
            INSERT INTO sales (customer_id, user_id, sale_date, total_amount, paymaent_method, payment_status)
            VALUES (%s, %s, CURDATE(), %s, %s, %s)
        """, (customer_id, user_id, total_amount, payment_method, payment_status))
        sale_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO `sale items` (sale_id, watch_id, quantity, unit_price, subtotal)
            VALUES (%s, %s, %s, %s, %s)
        """, (sale_id, watch_id, quantity, watch['selling_price'], total_amount))

        cursor.execute("SELECT inventory_id, quantity FROM inventory WHERE watch_id = %s AND quantity > 0 ORDER BY date_added ASC FOR UPDATE", (watch_id,))
        inv_rows = cursor.fetchall()
        rem = quantity
        for inv in inv_rows:
            if rem <= 0: break
            inv_id = inv['inventory_id']
            iq = inv['quantity']
            if iq <= rem:
                rem -= iq
                cursor.execute("UPDATE inventory SET quantity = 0, inventory_status = 'Out of Stock' WHERE inventory_id = %s", (inv_id,))
            else:
                cursor.execute("UPDATE inventory SET quantity = quantity - %s WHERE inventory_id = %s", (rem, inv_id))
                rem = 0

        cursor.execute("SELECT COALESCE(SUM(quantity), 0) as rem_stock FROM inventory WHERE watch_id = %s", (watch_id,))
        rem_stock = int(cursor.fetchone()['rem_stock'])
        if rem_stock <= 0:
            cursor.execute("UPDATE watches SET status = 'Sold Out' WHERE watch_id = %s", (watch_id,))

        return sale_id

    sale_id = db.execute_transaction(do_instore_sale)
    if sale_id:
        flash("Sale processed successfully.", "success")
        return redirect(url_for('view_receipt', sale_id=sale_id))
    else:
        flash("Failed to process sale. Check stock availability.", "error")
        return redirect(url_for('sales'))

# ==========================================
# RECEIPT VIEWING & DETAILS
# ==========================================
@app.route('/sales/receipt/<int:sale_id>')
def view_receipt(sale_id):
    sale = db.fetch_one("""
        SELECT s.*, c.full_name as customer_name, c.email as customer_email, 
               c.contact_number as customer_phone, c.address as customer_address,
               u.full_name as staff_name, u.user_name as staff_username
        FROM sales s
        JOIN customer c ON s.customer_id = c.customer_id
        LEFT JOIN user u ON s.user_id = u.user_id
        WHERE s.sale_id = %s
    """, (sale_id,))

    if not sale:
        flash("Sale record not found.", "error")
        return redirect(url_for('sales'))

    items = db.fetch_all("""
        SELECT si.*, w.brand, w.model, w.reference_number, w.watch_type 
        FROM `sale items` si
        JOIN watches w ON si.watch_id = w.watch_id
        WHERE si.sale_id = %s
    """, (sale_id,))

    return render_template('receipt.html', sale=sale, items=items)

@app.route('/api/sale/<int:sale_id>')
@login_required
def get_sale_api(sale_id):
    sale = db.fetch_one("""
        SELECT s.*, c.full_name as customer, u.full_name as staff
        FROM sales s
        JOIN customer c ON s.customer_id = c.customer_id
        LEFT JOIN user u ON s.user_id = u.user_id
        WHERE s.sale_id = %s
    """, (sale_id,))
    if not sale:
        return jsonify({"error": "Sale not found"}), 404

    items = db.fetch_all("""
        SELECT si.*, w.brand, w.model, w.reference_number 
        FROM `sale items` si
        JOIN watches w ON si.watch_id = w.watch_id
        WHERE si.sale_id = %s
    """, (sale_id,))
    
    sale['total_amount'] = float(sale['total_amount'])
    sale['items'] = items
    return jsonify(sale)

# ==========================================
# REPORTS & EXPORT FUNCTIONALITY
# ==========================================
@app.route('/reports')
@login_required
def reports():
    daily_sales = db.fetch_all("""
        SELECT sale_date, SUM(total_amount) as total, COUNT(*) as transactions 
        FROM sales 
        GROUP BY sale_date 
        ORDER BY sale_date DESC LIMIT 14
    """)
    
    revenue_by_brand = db.fetch_all("""
        SELECT w.brand, SUM(si.subtotal) as total, COUNT(si.sale_item_id) as units_sold
        FROM `sale items` si
        JOIN watches w ON si.watch_id = w.watch_id
        GROUP BY w.brand
        ORDER BY total DESC
    """)

    top_selling_watches = db.fetch_all("""
        SELECT w.brand, w.model, w.reference_number, 
               SUM(si.quantity) as total_units, 
               SUM(si.subtotal) as total_revenue
        FROM `sale items` si
        JOIN watches w ON si.watch_id = w.watch_id
        GROUP BY w.watch_id
        ORDER BY total_revenue DESC
        LIMIT 5
    """)

    inventory_valuation = db.fetch_one("""
        SELECT 
            COALESCE(SUM(i.quantity * w.purchase_price), 0) as total_cost_value,
            COALESCE(SUM(i.quantity * w.selling_price), 0) as total_retail_value,
            COALESCE(SUM(i.quantity), 0) as total_units_in_stock
        FROM inventory i
        JOIN watches w ON i.watch_id = w.watch_id
        WHERE i.inventory_status = 'In Stock'
    """)

    services_summary = db.fetch_all("""
        SELECT service_type, COUNT(*) as count, SUM(service_cost) as total_cost 
        FROM watch_services 
        GROUP BY service_type
    """)

    total_revenue_all = db.fetch_one("SELECT COALESCE(SUM(total_amount), 0) as total FROM sales WHERE payment_status = 'Paid'")['total']

    return render_template('reports.html', 
                           daily_sales=daily_sales, 
                           revenue_by_brand=revenue_by_brand,
                           top_selling_watches=top_selling_watches,
                           inventory_valuation=inventory_valuation,
                           services_summary=services_summary,
                           total_revenue_all=total_revenue_all)

@app.route('/reports/export/sales-csv')
@login_required
def export_sales_csv():
    sales = db.fetch_all("""
        SELECT s.sale_id, s.sale_date, c.full_name as customer, u.full_name as staff,
               s.paymaent_method, s.payment_status, s.total_amount
        FROM sales s
        JOIN customer c ON s.customer_id = c.customer_id
        LEFT JOIN user u ON s.user_id = u.user_id
        ORDER BY s.sale_date DESC, s.sale_id DESC
    """)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Sale ID', 'Date', 'Customer Name', 'Handled By', 'Payment Method', 'Payment Status', 'Total Amount (PHP)'])

    for s in sales:
        writer.writerow([
            f"#{s['sale_id']:04d}",
            s['sale_date'],
            s['customer'],
            s['staff'] or 'Online Storefront',
            s['paymaent_method'],
            s['payment_status'],
            f"{float(s['total_amount']):.2f}"
        ])

    output.seek(0)
    filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})

@app.route('/reports/export/inventory-csv')
@login_required
def export_inventory_csv():
    inv = db.fetch_all("""
        SELECT i.inventory_id, w.brand, w.model, w.reference_number, w.selling_price,
               i.quantity, i.location, i.inventory_status, i.date_added
        FROM inventory i
        JOIN watches w ON i.watch_id = w.watch_id
        ORDER BY w.brand, w.model
    """)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Inventory ID', 'Brand', 'Model', 'Reference Number', 'Selling Price (PHP)', 'Quantity in Stock', 'Location', 'Status', 'Date Added'])

    for item in inv:
        writer.writerow([
            f"#{item['inventory_id']:04d}",
            item['brand'],
            item['model'],
            item['reference_number'],
            f"{float(item['selling_price']):.2f}",
            item['quantity'],
            item['location'],
            item['inventory_status'],
            item['date_added']
        ])

    output.seek(0)
    filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})

@app.route('/reports/export/services-csv')
@login_required
def export_services_csv():
    srv = db.fetch_all("""
        SELECT ws.service_id, w.brand, w.model, c.full_name as customer,
               ws.service_type, ws.service_description, ws.service_date, ws.service_cost, ws.service_status
        FROM watch_services ws
        LEFT JOIN watches w ON ws.watch_id = w.watch_id
        LEFT JOIN customer c ON ws.customer_id = c.customer_id
        ORDER BY ws.service_date DESC
    """)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Service ID', 'Timepiece', 'Customer', 'Service Type', 'Description', 'Date', 'Cost (PHP)', 'Status'])

    for s in srv:
        timepiece = f"{s['brand']} {s['model']}" if s['brand'] else "N/A"
        writer.writerow([
            f"#{s['service_id']:04d}",
            timepiece,
            s['customer'] or "N/A",
            s['service_type'],
            s['service_description'],
            s['service_date'],
            f"{float(s['service_cost']):.2f}",
            s['service_status']
        ])

    output.seek(0)
    filename = f"services_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})

# Auto-initialize database tables if not yet created (useful for Railway deployment)
try:
    db.init_db()
except Exception as e:
    print(f"Schema init warning: {e}")

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
