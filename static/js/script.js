document.addEventListener('DOMContentLoaded', () => {
    // 1. Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(100%)';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });

    // 2. Universal Modal Logic
    const modals = document.querySelectorAll('.modal-overlay');
    const modalTriggers = document.querySelectorAll('[data-modal]');
    const modalCloses = document.querySelectorAll('.modal-close, [data-close-modal]');

    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const modalId = trigger.getAttribute('data-modal');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
            }
        });
    });

    modalCloses.forEach(close => {
        close.addEventListener('click', (e) => {
            e.preventDefault();
            const modal = close.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Close on backdrop click
    modals.forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    // 3. Watch Details Modal (Fetch via AJAX)
    const viewWatchBtns = document.querySelectorAll('.view-watch-btn');
    viewWatchBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const watchId = btn.getAttribute('data-id');
            try {
                const response = await fetch(`/api/watch/${watchId}`);
                if (response.ok) {
                    const data = await response.json();
                    populateWatchViewModal(data);
                    document.getElementById('watchDetailModal').classList.add('active');
                }
            } catch (error) {
                console.error("Failed to fetch watch details", error);
            }
        });
    });

    // 4. Edit Watch Modal
    const editWatchBtns = document.querySelectorAll('.edit-watch-btn');
    editWatchBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const watchId = btn.getAttribute('data-id');
            try {
                const response = await fetch(`/api/watch/${watchId}`);
                if (response.ok) {
                    const data = await response.json();
                    const form = document.getElementById('editWatchForm');
                    form.action = `/watches/edit/${data.watch_id}`;
                    document.getElementById('ew-brand').value = data.brand || '';
                    document.getElementById('ew-model').value = data.model || '';
                    document.getElementById('ew-reference').value = data.reference_number || '';
                    document.getElementById('ew-type').value = data.watch_type || '';
                    document.getElementById('ew-movement').value = data.movement || '';
                    document.getElementById('ew-condition').value = data.condition_status || '';
                    document.getElementById('ew-purchase').value = data.purchase_price || '';
                    document.getElementById('ew-selling').value = data.selling_price || '';
                    document.getElementById('ew-year').value = data.year_aquired || '';
                    document.getElementById('ew-status').value = data.status || 'Available';
                    document.getElementById('ew-desc').value = data.description || '';
                    document.getElementById('editWatchModal').classList.add('active');
                }
            } catch (error) {
                console.error("Failed to fetch watch for edit", error);
            }
        });
    });

    // 5. Edit Inventory Modal
    const editInvBtns = document.querySelectorAll('.edit-inv-btn');
    editInvBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const invId = btn.getAttribute('data-id');
            try {
                const response = await fetch(`/api/inventory/${invId}`);
                if (response.ok) {
                    const data = await response.json();
                    const form = document.getElementById('editInventoryForm');
                    form.action = `/inventory/edit/${data.inventory_id}`;
                    document.getElementById('ei_watch_name').textContent = `${data.brand} ${data.model} (Ref: ${data.reference_number})`;
                    document.getElementById('ei_quantity').value = data.quantity;
                    document.getElementById('ei_location').value = data.location;
                    document.getElementById('ei_status').value = data.inventory_status;
                    document.getElementById('editInventoryModal').classList.add('active');
                }
            } catch (error) {
                console.error("Failed to fetch inventory for edit", error);
            }
        });
    });

    // 6. Edit Customer Modal
    const editCustBtns = document.querySelectorAll('.edit-customer-btn');
    editCustBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const custId = btn.getAttribute('data-id');
            try {
                const response = await fetch(`/api/customer/${custId}`);
                if (response.ok) {
                    const data = await response.json();
                    const form = document.getElementById('editCustomerForm');
                    form.action = `/customers/edit/${data.customer_id}`;
                    document.getElementById('ec_name').value = data.full_name || '';
                    document.getElementById('ec_phone').value = data.contact_number || '';
                    document.getElementById('ec_email').value = data.email || '';
                    document.getElementById('ec_address').value = data.address || '';
                    document.getElementById('ec_type').value = data.customer_type || 'Regular';
                    document.getElementById('editCustomerModal').classList.add('active');
                }
            } catch (error) {
                console.error("Failed to fetch customer for edit", error);
            }
        });
    });

    // 7. Customer Purchase & Service History Modal
    const viewCustHistoryBtns = document.querySelectorAll('.view-customer-history-btn');
    viewCustHistoryBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const custId = btn.getAttribute('data-id');
            try {
                const response = await fetch(`/api/customer/${custId}`);
                if (response.ok) {
                    const data = await response.json();
                    document.getElementById('ch_title').textContent = `${data.full_name} - Client History`;
                    document.getElementById('ch_email').textContent = data.email;
                    document.getElementById('ch_phone').textContent = data.contact_number;
                    document.getElementById('ch_type').textContent = data.customer_type;
                    document.getElementById('ch_reg').textContent = data.date_registered;
                    document.getElementById('ch_address').textContent = data.address;

                    // Populate Orders
                    const ordersContainer = document.getElementById('ch_orders_container');
                    if (data.orders && data.orders.length > 0) {
                        let html = '<table class="data-table" style="font-size: 13px;"><thead><tr><th>Receipt #</th><th>Date</th><th>Amount</th><th>Method</th><th>Status</th></tr></thead><tbody>';
                        data.orders.forEach(o => {
                            html += `<tr>
                                <td>#${String(o.sale_id).padStart(4, '0')}</td>
                                <td>${o.sale_date}</td>
                                <td>₱ ${parseFloat(o.total_amount).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
                                <td>${o.paymaent_method}</td>
                                <td><span class="badge ${o.payment_status === 'Paid' ? 'badge-success' : 'badge-warning'}">${o.payment_status}</span></td>
                            </tr>`;
                        });
                        html += '</tbody></table>';
                        ordersContainer.innerHTML = html;
                    } else {
                        ordersContainer.innerHTML = '<p class="text-muted" style="font-size: 13px;">No past purchase transactions logged.</p>';
                    }

                    // Populate Services
                    const servicesContainer = document.getElementById('ch_services_container');
                    if (data.services && data.services.length > 0) {
                        let html = '<table class="data-table" style="font-size: 13px;"><thead><tr><th>Job #</th><th>Timepiece</th><th>Service</th><th>Date</th><th>Cost</th><th>Status</th></tr></thead><tbody>';
                        data.services.forEach(s => {
                            html += `<tr>
                                <td>#${String(s.service_id).padStart(4, '0')}</td>
                                <td>${s.brand || ''} ${s.model || ''}</td>
                                <td>${s.service_type}</td>
                                <td>${s.service_date}</td>
                                <td>₱ ${parseFloat(s.service_cost).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
                                <td><span class="badge ${s.service_status === 'Completed' ? 'badge-success' : 'badge-warning'}">${s.service_status}</span></td>
                            </tr>`;
                        });
                        html += '</tbody></table>';
                        servicesContainer.innerHTML = html;
                    } else {
                        servicesContainer.innerHTML = '<p class="text-muted" style="font-size: 13px;">No repair or maintenance jobs recorded.</p>';
                    }

                    document.getElementById('customerHistoryModal').classList.add('active');
                }
            } catch (error) {
                console.error("Failed to load customer history", error);
            }
        });
    });

    // 8. Edit User Modal
    const editUserBtns = document.querySelectorAll('.edit-user-btn');
    editUserBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const userId = btn.getAttribute('data-id');
            try {
                const response = await fetch(`/api/user/${userId}`);
                if (response.ok) {
                    const data = await response.json();
                    const form = document.getElementById('editUserForm');
                    form.action = `/users/edit/${data.user_id}`;
                    document.getElementById('eu_fullname').value = data.full_name || '';
                    document.getElementById('eu_username_display').value = data.user_name || '';
                    document.getElementById('eu_email').value = data.email || '';
                    document.getElementById('eu_role').value = data.role || 'Sales Staff';
                    document.getElementById('eu_status').value = data.status || 'Active';
                    document.getElementById('eu_pwd').value = '';
                    document.getElementById('editUserModal').classList.add('active');
                }
            } catch (error) {
                console.error("Failed to fetch user for edit", error);
            }
        });
    });

    // 9. Edit Watch Service Modal
    const editServiceBtns = document.querySelectorAll('.edit-service-btn');
    editServiceBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const serviceId = btn.getAttribute('data-id');
            try {
                const response = await fetch(`/api/service/${serviceId}`);
                if (response.ok) {
                    const data = await response.json();
                    const form = document.getElementById('editServiceForm');
                    form.action = `/services/edit/${data.service_id}`;
                    document.getElementById('es_info_display').textContent = `Client: ${data.customer_name || 'N/A'} • Watch: ${data.brand || ''} ${data.model || ''}`;
                    document.getElementById('es_type').value = data.service_type || '';
                    document.getElementById('es_cost').value = data.service_cost || '';
                    document.getElementById('es_date').value = data.service_date || '';
                    document.getElementById('es_status').value = data.service_status || 'Pending';
                    document.getElementById('es_desc').value = data.service_description || '';
                    document.getElementById('editServiceModal').classList.add('active');
                }
            } catch (error) {
                console.error("Failed to fetch service for edit", error);
            }
        });
    });

    // 10. Edit Investor Modal
    const editInvestorBtns = document.querySelectorAll('.edit-investor-btn');
    editInvestorBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const invId = btn.getAttribute('data-id');
            try {
                const response = await fetch(`/api/investor/${invId}`);
                if (response.ok) {
                    const data = await response.json();
                    const form = document.getElementById('editInvestorForm');
                    form.action = `/investors/edit/${data.investor_id}`;
                    document.getElementById('ei_name').value = data.investor_name || '';
                    document.getElementById('ei_contact').value = data.contact_number || '';
                    document.getElementById('ei_email').value = data.email || '';
                    document.getElementById('ei_amt').value = data.investment_amount || '';
                    document.getElementById('ei_date').value = data.investment_date || '';
                    document.getElementById('ei_status').value = data.investment_status || 'Active';
                    document.getElementById('editInvestorModal').classList.add('active');
                }
            } catch (error) {
                console.error("Failed to fetch investor for edit", error);
            }
        });
    });

    // 11. View Sale Details Modal
    const viewSaleBtns = document.querySelectorAll('.view-sale-details-btn');
    viewSaleBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const saleId = btn.getAttribute('data-id');
            try {
                const response = await fetch(`/api/sale/${saleId}`);
                if (response.ok) {
                    const data = await response.json();
                    document.getElementById('sd_sale_id').textContent = `#${String(data.sale_id).padStart(4, '0')}`;
                    document.getElementById('sd_customer').textContent = data.customer;
                    document.getElementById('sd_staff').textContent = data.staff || 'Online Storefront';
                    document.getElementById('sd_date').textContent = data.sale_date;
                    document.getElementById('sd_method').textContent = `${data.paymaent_method} (${data.payment_status})`;
                    document.getElementById('sd_total').textContent = `₱ ${parseFloat(data.total_amount).toLocaleString(undefined, {minimumFractionDigits: 2})}`;
                    document.getElementById('sd_receipt_link').href = `/sales/receipt/${data.sale_id}`;

                    let itemsHtml = '<table class="data-table" style="font-size: 13px;"><thead><tr><th>Timepiece</th><th>Ref</th><th>Qty</th><th>Unit</th><th>Subtotal</th></tr></thead><tbody>';
                    data.items.forEach(it => {
                        itemsHtml += `<tr>
                            <td><strong>${it.brand}</strong> ${it.model}</td>
                            <td><code>${it.reference_number}</code></td>
                            <td>${it.quantity}</td>
                            <td>₱ ${parseFloat(it.unit_price).toLocaleString()}</td>
                            <td><strong>₱ ${parseFloat(it.subtotal).toLocaleString()}</strong></td>
                        </tr>`;
                    });
                    itemsHtml += '</tbody></table>';
                    document.getElementById('sd_items_container').innerHTML = itemsHtml;

                    document.getElementById('saleDetailsModal').classList.add('active');
                }
            } catch (error) {
                console.error("Failed to fetch sale details", error);
            }
        });
    });

    // 12. In-Store Sale Dynamic Total Calculation
    const watchSelect = document.getElementById('new_sale_watch');
    const quantityInput = document.getElementById('new_sale_quantity');
    const totalDisplay = document.getElementById('new_sale_total');
    
    if (watchSelect && quantityInput && totalDisplay) {
        const calculateTotal = () => {
            const option = watchSelect.options[watchSelect.selectedIndex];
            if (option && option.value) {
                const price = parseFloat(option.getAttribute('data-price')) || 0;
                const maxStock = parseInt(option.getAttribute('data-stock')) || 1;
                let qty = parseInt(quantityInput.value) || 1;
                if (qty > maxStock) {
                    qty = maxStock;
                    quantityInput.value = maxStock;
                }
                const total = price * qty;
                totalDisplay.textContent = '₱ ' + total.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            } else {
                totalDisplay.textContent = '₱ 0.00';
            }
        };

        watchSelect.addEventListener('change', calculateTotal);
        quantityInput.addEventListener('input', calculateTotal);
    }

    // 13. Interactive Floating Watch Showcase (Storefront Hero)
    const heroCardContainer = document.getElementById('heroCardContainer');
    const floatingImg = document.querySelector('.hero-watch-floating-img');

    if (heroCardContainer && floatingImg) {
        heroCardContainer.addEventListener('mousemove', (e) => {
            const rect = heroCardContainer.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const moveX = ((x - centerX) / centerX) * 8;
            const moveY = ((y - centerY) / centerY) * 8;
            
            floatingImg.style.transform = `translate(${moveX.toFixed(1)}px, ${moveY.toFixed(1)}px) scale(1.03)`;
        });

        heroCardContainer.addEventListener('mouseleave', () => {
            floatingImg.style.transform = 'translate(0px, 0px) scale(1)';
        });
    }
});

function populateWatchViewModal(data) {
    document.getElementById('wd-full-title').textContent = `${data.brand} ${data.model}`;
    document.getElementById('wd-reference').textContent = data.reference_number;
    document.getElementById('wd-type').textContent = data.watch_type;
    document.getElementById('wd-movement').textContent = data.movement;
    document.getElementById('wd-condition').textContent = data.condition_status;
    document.getElementById('wd-purchase').textContent = data.purchase_price_formatted;
    document.getElementById('wd-selling').textContent = data.selling_price_formatted;
    document.getElementById('wd-year').textContent = data.year_aquired;
    document.getElementById('wd-status').textContent = data.status;
    document.getElementById('wd-location').textContent = data.sample_location || 'Showroom Cabinet';
    document.getElementById('wd-desc').textContent = data.description || 'Verified authentic vintage timepiece.';
    
    const stockEl = document.getElementById('wd-stock');
    stockEl.textContent = `${data.current_stock} in stock`;
    if (data.current_stock > 0) {
        stockEl.className = 'badge badge-success';
    } else {
        stockEl.className = 'badge badge-danger';
    }

    const imgContainer = document.getElementById('wd-image-container');
    if (data.image) {
        imgContainer.innerHTML = `<img src="/static/uploads/watches/${data.image}" alt="${data.brand}" style="width: 100%; height: 100%; object-fit: cover;">`;
    } else {
        imgContainer.innerHTML = '<i class="fas fa-clock" style="font-size: 40px; color: var(--color-accent);"></i>';
    }
}
