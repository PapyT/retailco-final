# RetailCo Analytics — Key Insights

## 1. Sales Performance

Sales performance is concentrated in Lagos and Abuja, which generate the highest transaction volumes, consistent with their position as major commercial and population centres. Port Harcourt processes fewer transactions but demonstrates stronger average order values, suggesting greater spending per customer and stronger performance for premium products.

At the product level, a relatively small number of categories contribute a disproportionate share of overall revenue. High-volume products are not always the most profitable, as aggressive discounting reduces realised revenue and margin.

Seasonal demand spikes are clearly visible around key national holidays — Democracy Day, Independence Day, Christmas, and Boxing Day — and should be factored into inventory planning and promotional campaigns.

**Recommendation:** Expand inventory and operational capacity in Lagos and Abuja to support demand growth. Identify premium product categories that perform well in Port Harcourt and replicate those offerings across other locations where appropriate.

---

## 2. Customer Behaviour

RetailCo currently serves approximately 5,000 customers across multiple segments. Premium customers purchase more frequently, complete transactions faster, and generate substantially higher average order values — in many cases two to three times more per order than standard-tier customers.

A notable cohort of customers transitions from standard to premium status over time, representing an important growth segment given their increasing purchasing activity and long-term value.

Delivery performance is also a meaningful retention driver. Customers whose orders are fulfilled within three days show higher repeat purchase rates than those experiencing longer delivery timelines.

**Recommendation:** Develop loyalty and retention programmes targeted at customers approaching premium status. Improving delivery speed and consistency should remain a priority, as fulfilment performance directly influences repeat purchases and customer satisfaction.

---

## 3. Product and Discount Analysis

Discounting remains a major driver of sales volume across several product categories. While discounts successfully increase transaction counts, they also compress margins and reduce realised revenue. Certain categories rely heavily on promotional pricing to generate demand, resulting in lower profitability despite strong sales volumes.

A clear distinction exists between top-selling products and top-performing products. High-volume products are not necessarily the most profitable; the strongest performers rank highly in both sales volume and net revenue.

**Recommendation:** Review products with the highest discount frequency and assess whether current pricing strategies are sustainable. Establish minimum margin thresholds for promotional campaigns and prioritise investment in products that consistently deliver strong volume and strong profitability.

---

## 4. Payment Channel Insights

RetailCo recorded approximately 71,900 payment events across five channels. Digital payment methods — mobile payments, card transactions, and bank transfers — account for the majority of transactions, reflecting broader trends in Nigerian consumer behaviour and increasing adoption of electronic payment solutions.

Refund transactions represent a small but important share of payment activity, providing useful indicators of customer experience and operational effectiveness.

Approximately 1,482 anomalous payment records were identified, representing roughly 2% of total payment activity. These include zero-value payments and unexplained negative payment amounts. While excluded from revenue reporting, they warrant further operational review.

**Recommendation:** Investigate anomalous payment activity to determine root causes and prevent recurrence. Introduce automated monitoring and alerting to identify unusual payment patterns in near real time.

---

## 5. Operational Data Quality

The data platform incorporates multiple layers of quality control. Extraction processes handle late-arriving records, transient system failures, and API rate limits while maintaining complete historical records. Transformations standardise formats, validate relationships, and isolate invalid records from production reporting.

The most significant anomaly identified involves payment-related exceptions, which account for approximately 2% of total payment records. Rather than removing these records, the platform isolates and tracks them for investigation while preventing them from distorting business metrics.

Overall, more than 98% of records pass through the platform into analytical models without issue, indicating a high level of data quality and confidence in reported results.

**Recommendation:** Continue monitoring data quality metrics as a formal operational KPI, with particular attention to payment anomalies and inventory discrepancies to ensure long-term reporting accuracy.

---

## Conclusion

The RetailCo analytics platform provides a reliable foundation for decision-making across sales, customer engagement, product strategy, payment operations, and data governance. Key findings point to strong revenue performance in major urban markets, meaningful growth opportunities among emerging premium customers, the need for tighter discount controls, growing digital payment adoption, and generally high data quality across the organisation.
