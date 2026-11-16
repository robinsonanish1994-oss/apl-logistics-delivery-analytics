# Video Scripts

## Video 1: Project Explanation (target 6–8 minutes)

**Setup:** screen-record the live Streamlit app and the GitHub repo. Keep your webcam in a corner if you can.

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:30 | Your face / title slide | "Hi, I'm [Name]. In this video I'll walk you through my internship project with Unified Mentor and APL Logistics: *Delivery Performance, Delay Risk and Logistics Efficiency Analysis in Global Supply Chain Operations*." |
| 0:30–1:15 | Research paper, page 1 | "APL Logistics ships high volumes across many regions. Late deliveries mean SLA penalties and unhappy customers, but the team had no clear view of how often deliveries are late, why, or where. I set out to answer five questions: the on-time percentage, which shipping modes are slowest, which geographies are riskiest, how segments are affected, and what to improve." |
| 1:15–2:00 | GitHub repo → `src/data_prep.py` | "The dataset has about 180,000 order records and 40 columns. I validated the shipping-day values and removed 7,754 cancelled shipments, because they never completed delivery. I cross-checked the late-risk flag against delivery status, translated 164 Spanish country names to English with ISO codes for the map, and dropped customer personal data. That leaves 172,765 delivered orders." |
| 2:00–2:30 | `src/kpis.py` | "The core metric is the Delay Gap: actual shipping days minus scheduled days. Below zero is early, zero is on time, above zero is delayed. From that I built five KPIs: on-time rate, average delay, late-risk ratio, a shipping-mode efficiency index and a regional delay index." |
| 2:30–3:30 | Dashboard → Performance Overview | "Here's the live dashboard. Only **42.7%** of orders arrive within the scheduled time. 57.3% are late, the average delay is +0.57 days, and a late order is 1.6 days behind. Late orders represent about $20 million in sales." |
| 3:30–4:30 | Delay Risk + Shipping Mode tabs | "The histogram shows a one-day overrun is the most common outcome. Shipping mode explains this. **First Class is late 100% of the time**: it always takes 2 days but promises 1. **Second Class is late about 80%** of the time, and its real transit time is exactly the same as Standard Class, 2 to 6 days. So the premium promise isn't backed by a faster lane." |
| 4:30–5:30 | Regional & Market Heatmaps | "Geographically, the five markets are almost identical at around 57%. Regions range from Canada at 51.6% to Central Africa at 60.1%. Western Europe and Germany matter because of their volume. I added a minimum-order slider so small countries don't create false alarms." |
| 5:30–6:00 | Sidebar → Customer segment filter (Corporate, then Consumer) | "Consumer, Corporate and Home Office customers are all late about 57% of the time. Delay depends on the shipping mode, not on who the customer is. That means corporate customers on First Class are guaranteed an SLA breach." |
| 6:00–6:30 | Use the sidebar filters live | "All charts respond to the filters: shipping mode, market, region, segment and SLA band. You can also download the filtered data." |
| 6:30–7:30 | Paper → Recommendations | "My recommendations: re-quote First Class at 2 days or build a real next-day lane; separate Second Class from Standard; add day-3 alerts for Standard; and run lane reviews in high-index regions. Resetting promises alone takes on-time delivery from 43% to about 60–68%, and fixing premium execution could reach about 74%." |
| 7:30–8:00 | Your face | "The tools I used were Python, pandas, Plotly, SciPy and Streamlit. The repo, paper and dashboard links are in my submission. Thank you!" |

---

## Video 2: Internship Experience & Feedback (target 2–3 minutes)

*Speak naturally and personalise the bracketed parts. Reviewers value honesty over polish.*

1. **Intro (15 s):** "Hi, I'm [Name], and I recently completed my data analytics internship with Unified Mentor, working on a project for APL Logistics."
2. **What I did (30 s):** "I analysed about 180,000 shipment records to find out why deliveries are late, built an interactive Streamlit dashboard, and wrote a research paper and an executive summary."
3. **Key learnings (45 s):**
   - "Technically, I improved my skills in pandas data cleaning, statistical testing with chi-square and Cramér's V, Plotly visualisation, and deploying an app on Streamlit Cloud."
   - "The biggest lesson was to question the data. I expected geography to drive delays, but the numbers showed the real issue was unrealistic shipping-mode promises."
   - "I also learned to explain results to non-technical stakeholders, which is why I wrote a separate executive summary."
4. **Challenges (30 s):** "[Example: the country names were in Spanish, so I built a mapping to English and ISO codes for the world map.] [Example: the dataset had no order date, so I made the date filter activate automatically when date data is available.]"
5. **Feedback (30 s):** "What I liked: [real-world dataset / clear project guide / mentor support / flexible schedule]. One suggestion: [e.g., more live doubt-clearing sessions or sample submissions]."
6. **Close (10 s):** "Overall it was a valuable, hands-on experience, and I'm grateful to Unified Mentor for the opportunity. Thank you!"

### Recording tips
- Use OBS Studio, Loom or the Windows/Mac built-in screen recorder at 1080p.
- Upload to YouTube as **Unlisted**, or to Google Drive with sharing set to **Anyone with the link → Viewer**.
- Test each link in a private/incognito window before submitting.
