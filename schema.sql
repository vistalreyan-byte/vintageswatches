-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 17, 2026 at 04:40 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `vintage_watches`
--

-- --------------------------------------------------------

--
-- Table structure for table `customer`
--

CREATE TABLE `customer` (
  `customer_id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `contact_number` varchar(20) NOT NULL,
  `email` varchar(100) NOT NULL,
  `address` varchar(255) NOT NULL,
  `customer_type` varchar(30) NOT NULL,
  `date_registered` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `customer`
--

INSERT INTO `customer` (`customer_id`, `full_name`, `contact_number`, `email`, `address`, `customer_type`, `date_registered`) VALUES
(1, 'Carlos Mendoza', '09171234567', 'carlos@gmail.com', 'Cebu City', 'Regular', '2026-01-05'),
(2, 'Miguel Santos', '09181234568', 'miguel@gmail.com', 'Tagbilaran City', 'VIP', '2026-01-08'),
(3, 'Daniel Cruz', '09191234569', 'daniel@gmail.com', 'Manila', 'Regular', '2026-01-12'),
(4, 'Robert Garcia', '09201234560', 'robert@gmail.com', 'Quezon City', 'VIP', '2026-01-15'),
(5, 'James Torres', '09211234561', 'james@gmail.com', 'Davao City', 'Regular', '2026-01-20'),
(6, 'Patrick Flores', '09221234562', 'patrick@gmail.com', 'Bacolod City', 'Regular', '2026-01-25'),
(7, 'Kevin Ramos', '09231234563', 'kevin@gmail.com', 'Cagayan de Oro', 'VIP', '2026-02-01'),
(8, 'Andrew Villanueva', '09241234564', 'andrew@gmail.com', 'Iloilo City', 'Regular', '2026-02-05'),
(9, 'Michael Aquino', '09251234565', 'michael@gmail.com', 'Makati City', 'VIP', '2026-02-10'),
(10, 'Anthony Bautista', '09261234566', 'anthony@gmail.com', 'Pasig City', 'Regular', '2026-02-15');

-- --------------------------------------------------------

--
-- Table structure for table `inventory`
--

CREATE TABLE `inventory` (
  `inventory_id` int(11) NOT NULL,
  `watch_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `location` varchar(100) NOT NULL,
  `date_added` date NOT NULL,
  `inventory_status` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `inventory`
--

INSERT INTO `inventory` (`inventory_id`, `watch_id`, `quantity`, `location`, `date_added`, `inventory_status`) VALUES
(1, 1, 1, 'Display Cabinet A', '2026-01-05', 'In Stock'),
(2, 2, 1, 'Display Cabinet A', '2026-01-06', 'In Stock'),
(3, 3, 3, 'Display Cabinet B', '2026-01-07', 'In Stock'),
(4, 4, 2, 'Display Cabinet B', '2026-01-08', 'In Stock'),
(5, 5, 4, 'Display Cabinet C', '2026-01-10', 'In Stock'),
(6, 6, 5, 'Display Cabinet C', '2026-01-11', 'In Stock'),
(7, 7, 3, 'Display Cabinet B', '2026-01-12', 'In Stock'),
(8, 8, 1, 'Display Cabinet A', '2026-01-15', 'In Stock'),
(9, 9, 2, 'Display Cabinet C', '2026-01-18', 'In Stock'),
(10, 10, 1, 'Display Cabinet A', '2026-01-20', 'In Stock');

-- --------------------------------------------------------

--
-- Table structure for table `investors`
--

CREATE TABLE `investors` (
  `investor_id` int(11) NOT NULL,
  `investor_name` varchar(100) NOT NULL,
  `contact_number` varchar(20) NOT NULL,
  `email` varchar(50) NOT NULL,
  `investment_amount` decimal(12,2) NOT NULL,
  `investment_date` date NOT NULL,
  `investment_status` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `investors`
--

INSERT INTO `investors` (`investor_id`, `investor_name`, `contact_number`, `email`, `investment_amount`, `investment_date`, `investment_status`) VALUES
(1, 'William Tan', '09170000001', 'william@gmail.com', 500000.00, '2026-01-05', 'Active'),
(2, 'Richard Lim', '09170000002', 'richard@gmail.com', 750000.00, '2026-01-06', 'Active'),
(3, 'George Sy', '09170000003', 'george@gmail.com', 1000000.00, '2026-01-08', 'Active'),
(4, 'Edward Chua', '09170000004', 'edward@gmail.com', 450000.00, '2026-01-10', 'Active'),
(5, 'Thomas Ong', '09170000005', 'thomas@gmail.com', 600000.00, '2026-01-12', 'Active'),
(6, 'Henry Go', '09170000006', 'henry@gmail.com', 850000.00, '2026-01-15', 'Active'),
(7, 'Joseph Uy', '09170000007', 'joseph@gmail.com', 350000.00, '2026-01-18', 'Active'),
(8, 'Francis Lee', '09170000008', 'francis@gmail.com', 900000.00, '2026-01-20', 'Active'),
(9, 'Albert Wong', '09170000009', 'albert@gmail.com', 550000.00, '2026-01-22', 'Active'),
(10, 'Steven Ho', '09170000010', 'steven@gmail.com', 700000.00, '2026-01-25', 'Active');

-- --------------------------------------------------------

--
-- Table structure for table `sale items`
--

CREATE TABLE `sale items` (
  `sale_item_id` int(11) NOT NULL,
  `sale_id` int(11) NOT NULL,
  `watch_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `unit_price` decimal(12,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `sale items`
--

INSERT INTO `sale items` (`sale_item_id`, `sale_id`, `watch_id`, `quantity`, `unit_price`, `subtotal`) VALUES
(1, 1, 1, 1, 450000.00, 450000.00),
(2, 2, 2, 1, 320000.00, 320000.00),
(3, 3, 3, 1, 35000.00, 35000.00),
(4, 4, 4, 1, 48000.00, 48000.00),
(5, 5, 5, 1, 22000.00, 22000.00),
(6, 6, 6, 1, 8500.00, 8500.00),
(7, 7, 7, 1, 18000.00, 18000.00),
(8, 8, 8, 1, 95000.00, 95000.00),
(9, 9, 9, 1, 42000.00, 42000.00),
(10, 10, 10, 1, 280000.00, 280000.00);

-- --------------------------------------------------------

--
-- Table structure for table `sales`
--

CREATE TABLE `sales` (
  `sale_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `sale_date` date NOT NULL,
  `total_amount` decimal(12,2) NOT NULL,
  `paymaent_method` varchar(30) NOT NULL,
  `payment_status` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `sales`
--

INSERT INTO `sales` (`sale_id`, `customer_id`, `user_id`, `sale_date`, `total_amount`, `paymaent_method`, `payment_status`) VALUES
(1, 1, 2, '2026-02-01', 450000.00, 'Bank Transfer', 'Paid'),
(2, 2, 2, '2026-02-03', 320000.00, 'Cash', 'Paid'),
(3, 3, 3, '2026-02-05', 35000.00, 'GCash', 'Paid'),
(4, 4, 2, '2026-02-07', 48000.00, 'Credit Card', 'Paid'),
(5, 5, 3, '2026-02-10', 22000.00, 'Cash', 'Paid'),
(6, 6, 2, '2026-02-12', 8500.00, 'GCash', 'Paid'),
(7, 7, 3, '2026-02-15', 18000.00, 'Cash', 'Paid'),
(8, 8, 2, '2026-02-18', 95000.00, 'Bank Transfer', 'Paid'),
(9, 9, 3, '2026-02-20', 42000.00, 'Credit Card', 'Paid'),
(10, 10, 2, '2026-02-22', 280000.00, 'Bank Transfer', 'Paid');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `user_id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `user_name` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(30) NOT NULL,
  `email` int(100) NOT NULL,
  `status` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`user_id`, `full_name`, `user_name`, `password`, `role`, `email`, `status`) VALUES
(1, 'Reyan Vistal', 'admin', 'admin123', 'Administrator', 0, 'Active'),
(2, 'Mark Santos', 'staff1', 'staff123', 'Sales Staff', 0, 'Active'),
(3, 'Anna Reyes', 'staff2', 'staff456', 'Sales Staff', 0, 'Active');

-- --------------------------------------------------------

--
-- Table structure for table `watches`
--

CREATE TABLE `watches` (
  `watch_id` int(11) NOT NULL,
  `brand` varchar(50) NOT NULL,
  `model` varchar(100) NOT NULL,
  `reference_number` varchar(50) NOT NULL,
  `watch_type` varchar(50) NOT NULL,
  `movement` varchar(50) NOT NULL,
  `condition_status` varchar(30) NOT NULL,
  `purchase_price` decimal(12,2) NOT NULL,
  `selling_price` decimal(12,2) NOT NULL,
  `year_aquired` year(4) NOT NULL,
  `status` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `watches`
--

INSERT INTO `watches` (`watch_id`, `brand`, `model`, `reference_number`, `watch_type`, `movement`, `condition_status`, `purchase_price`, `selling_price`, `year_aquired`, `status`) VALUES
(1, 'Rolex', 'Submariner Date', '116610LN', 'Diver', 'Automatic', 'Excellent', 380000.00, 450000.00, '2024', 'Available'),
(2, 'Omega', 'Seamaster Professional', '210.30.42.20.01.001', 'Diver', 'Automatic', 'Excellent', 270000.00, 320000.00, '2024', 'Available'),
(3, 'Seiko', 'Presage Cocktail Time', 'SRPB43J1', 'Dress Watch', 'Automatic', 'Very Good', 25000.00, 35000.00, '2025', 'Available'),
(4, 'Tissot', 'PRX Powermatic 80', 'T1374071105100', 'Dress/Sport', 'Automatic', 'Excellent', 38000.00, 48000.00, '2025', 'Available'),
(5, 'Citizen', 'Eco-Drive Chronograph', 'CA0690-88E', 'Chronograph', 'Quartz', 'Very Good', 16000.00, 22000.00, '2025', 'Available'),
(6, 'Casio', 'G-Shock Mudmaster', 'GG-1000-1A3', 'Sports Watch', 'Quartz', 'Good', 6500.00, 8500.00, '2025', 'Available'),
(7, 'Orient', 'Bambino Version 4', 'FAC08003A0', 'Dress Watch', 'Automatic', 'Very Good', 13000.00, 18000.00, '2025', 'Available'),
(8, 'Longines', 'HydroConquest', 'L3.781.4.56.6', 'Diver', 'Automatic', 'Excellent', 78000.00, 95000.00, '2024', 'Available'),
(9, 'Hamilton', 'Khaki Field Automatic', 'H70455553', 'Field Watch', 'Automatic', 'Very Good', 35000.00, 42000.00, '2025', 'Available'),
(10, 'TAG Heuer', 'Carrera Calibre 5', 'WAR211A.FC6180', 'Dress/Sport', 'Automatic', 'Excellent', 230000.00, 280000.00, '2024', 'Available');

-- --------------------------------------------------------

--
-- Table structure for table `watch_services`
--

CREATE TABLE `watch_services` (
  `service_id` int(11) NOT NULL,
  `watch_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `service_type` varchar(100) NOT NULL,
  `service_description` varchar(255) NOT NULL,
  `service_date` date NOT NULL,
  `service_cost` decimal(12,2) NOT NULL,
  `service_status` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `watch_services`
--

INSERT INTO `watch_services` (`service_id`, `watch_id`, `customer_id`, `service_type`, `service_description`, `service_date`, `service_cost`, `service_status`) VALUES
(1, 1, 1, 'Cleaning', 'Complete exterior cleaning', '2026-02-02', 1500.00, 'Completed'),
(2, 2, 2, 'Maintenance', 'Automatic movement inspection', '2026-02-04', 3000.00, 'Completed'),
(3, 3, 3, 'Strap Replacement', 'Leather strap replacement', '2026-02-06', 1200.00, 'Completed'),
(4, 4, 4, 'Cleaning', 'Case and bracelet cleaning', '2026-02-08', 1000.00, 'Completed'),
(5, 5, 5, 'Battery Replacement', 'Battery replacement and testing', '2026-02-11', 800.00, 'Completed'),
(6, 6, 6, 'Cleaning', 'Deep cleaning service', '2026-02-13', 1000.00, 'Completed'),
(7, 7, 7, 'Strap Replacement', 'Replacement of leather strap', '2026-02-16', 1200.00, 'Completed'),
(8, 8, 8, 'Maintenance', 'Movement inspection and lubrication', '2026-02-19', 3500.00, 'Completed'),
(9, 9, 9, 'Cleaning', 'Case and crystal cleaning', '2026-02-21', 1000.00, 'Completed'),
(10, 10, 10, 'Maintenance', 'Full mechanical inspection', '2026-02-23', 4000.00, 'Completed');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `customer`
--
ALTER TABLE `customer`
  ADD PRIMARY KEY (`customer_id`);

--
-- Indexes for table `inventory`
--
ALTER TABLE `inventory`
  ADD PRIMARY KEY (`inventory_id`),
  ADD KEY `watch_id` (`watch_id`);

--
-- Indexes for table `investors`
--
ALTER TABLE `investors`
  ADD PRIMARY KEY (`investor_id`);

--
-- Indexes for table `sale items`
--
ALTER TABLE `sale items`
  ADD PRIMARY KEY (`sale_item_id`),
  ADD KEY `sale_id` (`sale_id`),
  ADD KEY `watch_id` (`watch_id`);

--
-- Indexes for table `sales`
--
ALTER TABLE `sales`
  ADD PRIMARY KEY (`sale_id`),
  ADD KEY `customer_id` (`customer_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`user_id`);

--
-- Indexes for table `watches`
--
ALTER TABLE `watches`
  ADD PRIMARY KEY (`watch_id`);

--
-- Indexes for table `watch_services`
--
ALTER TABLE `watch_services`
  ADD PRIMARY KEY (`service_id`),
  ADD KEY `watch_id` (`watch_id`),
  ADD KEY `customer_id` (`customer_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `inventory`
--
ALTER TABLE `inventory`
  MODIFY `inventory_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `investors`
--
ALTER TABLE `investors`
  MODIFY `investor_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `sale items`
--
ALTER TABLE `sale items`
  MODIFY `sale_item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `sales`
--
ALTER TABLE `sales`
  MODIFY `sale_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `watch_services`
--
ALTER TABLE `watch_services`
  MODIFY `service_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `inventory`
--
ALTER TABLE `inventory`
  ADD CONSTRAINT `fk_inventory_watch` FOREIGN KEY (`watch_id`) REFERENCES `watches` (`watch_id`);

--
-- Constraints for table `sale items`
--
ALTER TABLE `sale items`
  ADD CONSTRAINT `fk_sale_items_sale_id` FOREIGN KEY (`sale_id`) REFERENCES `sales` (`sale_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_sale_items_watch_id` FOREIGN KEY (`watch_id`) REFERENCES `watches` (`watch_id`);

--
-- Constraints for table `sales`
--
ALTER TABLE `sales`
  ADD CONSTRAINT `fk_sales_customer` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`),
  ADD CONSTRAINT `fk_sales_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
