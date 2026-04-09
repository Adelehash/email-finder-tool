import streamlit as st
import pandas as pd
import dns.resolver
import smtplib
import time

st.set_page_config(page_title="Email Finder", page_icon="📧")

st.title("📧 Email Finder + Verifier")

# -------- EMAIL PATTERNS --------
def generate_emails(first, last, domain):
    first = first.lower().strip()
    last = last.lower().strip()

    f = first[0] if first else ""
    l = last[0] if last else ""

    patterns = [
        f"{first}.{last}@{domain}",
        f"{f}.{last}@{domain}",
        f"{first}@{domain}",
        f"{f}{last}@{domain}",

        f"{first}_{last}@{domain}",
        f"{first}-{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{last}.{first}@{domain}",
        f"{last}{first}@{domain}",

        f"{first}.{l}@{domain}",
        f"{f}.{l}@{domain}",
        f"{f}{l}@{domain}",

        f"{first[0:2]}{last}@{domain}" if len(first) > 1 else "",
        f"{first}{last[0:2]}@{domain}" if len(last) > 1 else "",

        # Generic inboxes
        f"info@{domain}",
        f"contact@{domain}",
        f"hello@{domain}",
        f"admin@{domain}",
        f"sales@{domain}",
    ]

    return list(set([p for p in patterns if p]))

# -------- MX RECORD --------
def get_mx(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return str(records[0].exchange)
    except:
        return None

# -------- SMTP VERIFY --------
def verify_email(email, mx):
    try:
        server = smtplib.SMTP(timeout=10)
        server.connect(mx)
        server.helo("test.com")
        server.mail("test@test.com")
        code, _ = server.rcpt(email)
        server.quit()

        if code == 250:
            return "Valid"
        elif code == 550:
            return "Invalid"
        else:
            return "Unknown"
    except:
        return "Unknown"

# -------- CATCH-ALL CHECK --------
def is_catch_all(domain, mx):
    fake_email = f"random123456@{domain}"
    result = verify_email(fake_email, mx)
    return result == "Valid"

# -------- FIND BEST EMAILS --------
def find_emails(first, last, domain):
    mx = get_mx(domain)
    if not mx:
        return []

    catch_all = is_catch_all(domain, mx)
    emails = generate_emails(first, last, domain)

    valid_results = []

    for email in emails:
        status = verify_email(email, mx)

        if catch_all:
            status = "Catch-all"

        if status in ["Valid", "Catch-all"]:
            valid_results.append({
                "email": email,
                "status": status
            })

    return valid_results

# ============================
# 🔹 SINGLE FINDER
# ============================

st.subheader("🔍 Single Email Finder")

col1, col2 = st.columns(2)

first_name = col1.text_input("First Name")
last_name = col2.text_input("Last Name")
domain = st.text_input("Company Domain (e.g. shopify.com)")

if st.button("Find Email"):
    if not first_name or not last_name or not domain:
        st.warning("Please fill all fields")
    else:
        with st.spinner("Checking..."):
            results = find_emails(first_name, last_name, domain)

            if results:
                df = pd.DataFrame(results)
                st.success("Emails Found 🎉")
                st.dataframe(df)
            else:
                st.error("Emails not found")

# ============================
# 🔹 BULK FINDER
# ============================

st.divider()
st.subheader("📂 Bulk Email Finder")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if not all(col in df.columns for col in ["first_name", "last_name", "domain"]):
        st.error("CSV must have: first_name, last_name, domain")
    else:
        st.write(f"Total rows: {len(df)}")

        if st.button("Start Bulk Processing"):
            results = []

            with st.spinner("Processing..."):
                for _, row in df.iterrows():
                    first = row["first_name"]
                    last = row["last_name"]
                    domain = row["domain"]

                    found = find_emails(first, last, domain)

                    if found:
                        for r in found:
                            results.append(r)
                    else:
                        results.append({
                            "email": f"{first} {last} ({domain})",
                            "status": "Not Found"
                        })

                    time.sleep(2)

            result_df = pd.DataFrame(results)

            st.success("Done 🎉")
            st.dataframe(result_df)

            csv = result_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download Results",
                csv,
                "email_results.csv",
                "text/csv"
            )
