-- =====================================================================
-- ShopSphere: E-Commerce Sales & Profitability Analysis (MySQL 8+)
-- Data: data/cleaned_ecommerce_orders.csv (synthetic, generated with Python)
-- Note: Revenue/Profit are populated for ALL order statuses (including
--       Cancelled and Returned), so totals are not verified net sales.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. SETUP
-- ---------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS shopsphere;
USE shopsphere;

DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    OrderID        INT PRIMARY KEY,
    OrderDate      DATE,
    CustomerID     VARCHAR(20),
    CustomerName   VARCHAR(100),
    Product        VARCHAR(50),
    Category       VARCHAR(50),
    City           VARCHAR(50),
    Quantity       INT,
    UnitPrice      DECIMAL(12,2),
    Revenue        DECIMAL(14,2),
    Cost           DECIMAL(14,2),
    Profit         DECIMAL(14,2),
    PaymentMethod  VARCHAR(30),
    OrderStatus    VARCHAR(20),
    Discount       DECIMAL(4,2)
);

-- Import data/cleaned_ecommerce_orders.csv:
-- MySQL Workbench -> right-click table "orders" -> Table Data Import Wizard.
-- Map columns by name and leave extra CSV columns (Year, Month, MonthName,
-- DayOfWeek, ProfitMargin) unmapped. Adjust column names if yours differ.

-- ---------------------------------------------------------------------
-- 2. DATA-QUALITY CHECKS (every result should be 0)
-- ---------------------------------------------------------------------
SELECT 'duplicate OrderIDs' AS check_name, COUNT(*) - COUNT(DISTINCT OrderID) AS issues FROM orders
UNION ALL SELECT 'invalid quantity (<= 0)',  COUNT(*) FROM orders WHERE Quantity <= 0
UNION ALL SELECT 'missing customer name',    COUNT(*) FROM orders WHERE CustomerName IS NULL OR CustomerName = ''
UNION ALL SELECT 'missing city',             COUNT(*) FROM orders WHERE City IS NULL OR City = ''
UNION ALL SELECT 'missing unit price',       COUNT(*) FROM orders WHERE UnitPrice IS NULL
UNION ALL SELECT 'profit <> revenue - cost', COUNT(*) FROM orders WHERE ABS(Profit - (Revenue - Cost)) > 1;

-- ---------------------------------------------------------------------
-- 3. HEADLINE KPIs  (expect ~14,980 orders, ~INR 648.0M revenue, ~27.5% margin)
-- ---------------------------------------------------------------------
SELECT COUNT(DISTINCT OrderID)                       AS orders,
       COUNT(DISTINCT CustomerID)                    AS customers,
       ROUND(SUM(Revenue) / 1e6, 1)                  AS revenue_m,
       ROUND(SUM(Profit)  / 1e6, 1)                  AS profit_m,
       ROUND(SUM(Profit) / SUM(Revenue) * 100, 2)    AS margin_pct,
       ROUND(SUM(Revenue) / COUNT(DISTINCT OrderID)) AS avg_order_value,
       SUM(Quantity)                                 AS units_sold
FROM orders;

-- ---------------------------------------------------------------------
-- 4. PRODUCT PERFORMANCE: revenue, profit, margin and share of total
--    (expect Laptop first, ~269.0M revenue)
-- ---------------------------------------------------------------------
SELECT Product, Category,
       ROUND(SUM(Revenue) / 1e6, 2)                                   AS revenue_m,
       ROUND(SUM(Profit)  / 1e6, 2)                                   AS profit_m,
       ROUND(SUM(Profit) / SUM(Revenue) * 100, 2)                     AS margin_pct,
       ROUND(SUM(Revenue) / SUM(SUM(Revenue)) OVER () * 100, 1)       AS revenue_share_pct,
       ROUND(SUM(Profit)  / SUM(SUM(Profit))  OVER () * 100, 1)       AS profit_share_pct
FROM orders
GROUP BY Product, Category
ORDER BY revenue_m DESC;

-- ---------------------------------------------------------------------
-- 5. PROFIT CONCENTRATION: cumulative profit share by product
--    (expect Laptop ~41.5%, top 3 ~74%)
-- ---------------------------------------------------------------------
WITH product_profit AS (
    SELECT Product, SUM(Profit) AS profit
    FROM orders
    GROUP BY Product
)
SELECT Product,
       ROUND(profit / 1e6, 2)                                            AS profit_m,
       ROUND(profit / SUM(profit) OVER () * 100, 1)                      AS profit_share_pct,
       ROUND(SUM(profit) OVER (ORDER BY profit DESC)
             / SUM(profit) OVER () * 100, 1)                             AS cumulative_pct
FROM product_profit
ORDER BY profit DESC;

-- ---------------------------------------------------------------------
-- 6. MONTHLY TREND with month-over-month change (expect March peak, October low)
-- ---------------------------------------------------------------------
WITH monthly AS (
    SELECT DATE_FORMAT(OrderDate, '%Y-%m') AS month,
           SUM(Revenue) AS revenue,
           SUM(Profit)  AS profit,
           COUNT(DISTINCT OrderID) AS orders
    FROM orders
    GROUP BY DATE_FORMAT(OrderDate, '%Y-%m')
)
SELECT month,
       ROUND(revenue / 1e6, 2) AS revenue_m,
       ROUND(profit  / 1e6, 2) AS profit_m,
       orders,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month) * 100, 1) AS mom_revenue_change_pct
FROM monthly
ORDER BY month;

-- ---------------------------------------------------------------------
-- 7. CITY PERFORMANCE with rank
-- ---------------------------------------------------------------------
SELECT RANK() OVER (ORDER BY SUM(Revenue) DESC)       AS revenue_rank,
       City,
       ROUND(SUM(Revenue) / 1e6, 2)                   AS revenue_m,
       ROUND(SUM(Profit)  / 1e6, 2)                   AS profit_m,
       ROUND(SUM(Profit) / SUM(Revenue) * 100, 2)     AS margin_pct,
       COUNT(DISTINCT OrderID)                        AS orders
FROM orders
GROUP BY City
ORDER BY revenue_rank;

-- ---------------------------------------------------------------------
-- 8. TOP PRODUCT WITHIN EACH CATEGORY (window function)
-- ---------------------------------------------------------------------
WITH ranked AS (
    SELECT Category, Product, SUM(Revenue) AS revenue,
           ROW_NUMBER() OVER (PARTITION BY Category ORDER BY SUM(Revenue) DESC) AS rn
    FROM orders
    GROUP BY Category, Product
)
SELECT Category, Product, ROUND(revenue / 1e6, 2) AS revenue_m
FROM ranked
WHERE rn = 1;

-- ---------------------------------------------------------------------
-- 9. CUSTOMER SEGMENTS (one-time = 1 order, occasional = 2-4, frequent = 5+)
-- ---------------------------------------------------------------------
WITH customer_orders AS (
    SELECT CustomerID,
           COUNT(DISTINCT OrderID) AS orders,
           SUM(Revenue) AS revenue,
           SUM(Profit)  AS profit
    FROM orders
    GROUP BY CustomerID
)
SELECT CASE WHEN orders = 1 THEN 'One-time'
            WHEN orders BETWEEN 2 AND 4 THEN 'Occasional'
            ELSE 'Frequent' END                    AS segment,
       COUNT(*)                                    AS customers,
       ROUND(AVG(revenue))                         AS revenue_per_customer,
       ROUND(AVG(profit))                          AS profit_per_customer
FROM customer_orders
GROUP BY segment
ORDER BY revenue_per_customer DESC;

-- ---------------------------------------------------------------------
-- 10. TOP 10 CUSTOMERS BY REVENUE
-- ---------------------------------------------------------------------
SELECT CustomerID, CustomerName,
       COUNT(DISTINCT OrderID)        AS orders,
       ROUND(SUM(Revenue))            AS revenue,
       ROUND(SUM(Profit))             AS profit
FROM orders
GROUP BY CustomerID, CustomerName
ORDER BY revenue DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- 11. DISCOUNT LEVEL VS. MARGIN (descriptive only, not causal)
-- ---------------------------------------------------------------------
SELECT CONCAT(ROUND(Discount * 100), '%')            AS discount,
       COUNT(DISTINCT OrderID)                       AS orders,
       ROUND(SUM(Revenue) / 1e6, 2)                  AS revenue_m,
       ROUND(SUM(Profit) / SUM(Revenue) * 100, 2)    AS margin_pct
FROM orders
GROUP BY Discount
ORDER BY Discount;

-- ---------------------------------------------------------------------
-- 12. ORDER STATUS AND LEAKAGE (expect ~32.7% Cancelled + Returned)
-- ---------------------------------------------------------------------
SELECT OrderStatus,
       COUNT(DISTINCT OrderID) AS orders,
       ROUND(COUNT(DISTINCT OrderID) / SUM(COUNT(DISTINCT OrderID)) OVER () * 100, 1) AS share_pct,
       ROUND(SUM(Revenue) / 1e6, 1) AS revenue_m
FROM orders
GROUP BY OrderStatus
ORDER BY orders DESC;

-- ---------------------------------------------------------------------
-- 13. PAYMENT METHODS
-- ---------------------------------------------------------------------
SELECT PaymentMethod,
       COUNT(DISTINCT OrderID)        AS orders,
       ROUND(SUM(Revenue) / 1e6, 1)   AS revenue_m,
       ROUND(AVG(Revenue))            AS avg_order_value
FROM orders
GROUP BY PaymentMethod
ORDER BY orders DESC;
