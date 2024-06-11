import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urlparse, urljoin
import smtplib
from email.mime.text import MIMEText

# Initialize OpenAI API key
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""

# Initialize SMTP configurations
if "smtp_configs" not in st.session_state:
    st.session_state.smtp_configs = []

# Initialize domain data
if "domain_data" not in st.session_state:
    st.session_state.domain_data = []

# Initialize user information
if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "name": "",
        "business_name": "",
        "website": "",
        "business_description": "",
        "email": "",
        "phone_number": ""
    }

def show_settings():
    st.sidebar.title("⚙️ Settings")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", st.session_state.openai_api_key, type="password")
    if openai_api_key != st.session_state.openai_api_key:
        st.session_state.openai_api_key = openai_api_key

    st.sidebar.subheader("👤 User Information")
    st.session_state.user_info["name"] = st.sidebar.text_input("Name", st.session_state.user_info["name"])
    st.session_state.user_info["business_name"] = st.sidebar.text_input("Business Name", st.session_state.user_info["business_name"])
    st.session_state.user_info["website"] = st.sidebar.text_input("Website", st.session_state.user_info["website"])
    st.session_state.user_info["business_description"] = st.sidebar.text_area("Business Description", st.session_state.user_info["business_description"])
    st.session_state.user_info["email"] = st.sidebar.text_input("Email", st.session_state.user_info["email"])
    st.session_state.user_info["phone_number"] = st.sidebar.text_input("Phone Number", st.session_state.user_info["phone_number"])

    st.sidebar.subheader("📧 SMTP Configurations")
    smtp_configs = st.session_state.smtp_configs.copy()
    for i, config in enumerate(smtp_configs):
        with st.sidebar.expander(f"Configuration {i+1}"):
            config["server"] = st.text_input(f"SMTP Server {i+1}", config["server"])
            config["port"] = st.text_input(f"SMTP Port {i+1}", str(config["port"]))
            config["username"] = st.text_input(f"SMTP Username {i+1}", config["username"])
            config["password"] = st.text_input(f"SMTP Password {i+1}", config["password"], type="password")
            config["sender_email"] = st.text_input(f"Sender Email {i+1}", config["sender_email"])
            if st.button(f"Check Configuration {i+1}", key=f"check_config_{i}"):
                try:
                    if config["port"] == 465:  # Port 465 is for SMTP with SSL
                        smtp = smtplib.SMTP_SSL(config["server"], config["port"])
                    else:  # Port 587 is for SMTP with TLS
                        smtp = smtplib.SMTP(config["server"], config["port"])
                        smtp.starttls()
                    smtp.login(config["username"], config["password"])
                    smtp.quit()
                    st.success(f"✅ Configuration {i+1} is valid.")
                except smtplib.SMTPAuthenticationError:
                    st.error(f"❌ Authentication failed for Configuration {i+1}.")
                except Exception as e:
                    st.error(f"❌ Error checking Configuration {i+1}: {e}")
    st.session_state.smtp_configs = smtp_configs

    if st.sidebar.button("➕ Add SMTP Configuration"):
        st.session_state.smtp_configs.append({
            "server": "",
            "port": 587,
            "username": "",
            "password": "",
            "sender_email": ""
        })

st.set_page_config(page_title="Domain Scraper", page_icon="🌐", layout="wide")
st.markdown("""
<style>
.css-18e3th9 {
    padding-top: 1rem;
    padding-bottom: 10rem;
    background-color: #e6f2ff;
}
</style>
""", unsafe_allow_html=True)

show_settings()

st.title("🔍 Domain Scraper with Email Extraction and Personalized Outreach")

domains = st.text_area("Enter domains (one per line)")

def scrape_domains(domains):
    domain_data = []
    for domain in domains.split("\n"):
        try:
            parsed_url = urlparse(domain)
            if not parsed_url.scheme:
                url = f"https://{domain}"
            else:
                url = domain

            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            soup = BeautifulSoup(response.text, "html.parser")

            domain_name = parsed_url.netloc
            page_title = soup.find("title").get_text()
            meta_description = soup.find("meta", attrs={"name":"description"}).get("content", "")
            main_text = " ".join([p.get_text() for p in soup.find_all("p")])

            # Extract email addresses using multiple methods
            emails = set()

            # Method 1: Regular expression on HTML content
            emails.update(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", response.text))

            # Method 2: mailto: links
            mailto_links = soup.find_all("a", href=re.compile(r"mailto:"))
            emails.update([link.get("href").replace("mailto:", "") for link in mailto_links])

            # Method 3: Text content of HTML elements
            for element in soup.find_all(text=re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), recursive=True):
                emails.add(element)

            # Method 4: HTML attributes
            for tag in soup.find_all(True):
                for attr in tag.attrs.values():
                    emails.update(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", str(attr)))

            # Method 5: Find "Contact Us" page and extract emails
            contact_links = soup.find_all("a", string=re.compile(r"Contact( Us)?", re.IGNORECASE))
            for link in contact_links:
                contact_url = urljoin(url, link.get("href"))
                try:
                    contact_response = requests.get(contact_url)
                    contact_response.raise_for_status()
                    contact_soup = BeautifulSoup(contact_response.text, "html.parser")
                    emails.update(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", contact_soup.get_text()))
                except Exception as e:
                    st.warning(f"⚠️ Error retrieving contact page for {domain_name}: {e}")

            # Convert the set to a list
            emails = list(emails)

            # Generate personalized outreach using OpenAI API
            prompt =  prompt = f"Based on the following information:\n\nCompany Name: {company_name}\nProduct/Service Description: {product_description}\nTarget Industry: {target_industry}\n\nCraft a personalized and engaging cold email to potential customers in the {target_industry} industry. The email should introduce {company_name} and highlight the benefits of our product/service. Keep the email concise, persuasive, and actionable.\n\nAdditionally, please include a signature with the following details:\n\nName: [Your Name]\nCompany: {company_name}\nWebsite: [Your Website]\nEmail: [Your Email]\nPhone Number: [Your Phone Number]"
                "Content-Type": "application/json"
                "Authorization": f"Bearer {st.session_state.openai_api_key}"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "n": 1,
                "stop": None,
                "temperature": 0.7
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            outreach_email = response.json()["choices"][0]["message"]["content"].strip()

            # Ask OpenAI to suggest the best email for outreach
            email_prompt = f"Here are the email addresses found on the website {domain_name}:\n\n{', '.join(emails)}\n\nBased on the website content and the personalized outreach email, which email address would be the most appropriate to send the outreach to? Please make sure to only respond with the suggested email, nothing else!"
            email_data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": email_prompt}, {"role": "assistant", "content": outreach_email}],
                "max_tokens": 100,
                "n": 1,
                "stop": None,
                "temperature": 0.7
            }
            email_response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=email_data)
            email_response.raise_for_status()
            suggested_email = email_response.json()["choices"][0]["message"]["content"].strip()

            domain_data.append({
                "domain": domain_name,
                "outreach_email": outreach_email,
                "suggested_email": suggested_email
            })
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error scraping data for {domain}: {e}")
            logging.error(f"Error scraping {domain}: {e}")
        except Exception as e:
            st.error(f"❌ Error scraping data for {domain}: {e}")
            logging.error(f"Error scraping {domain}: {e}")

    return domain_data

def show_domain_data():
    if st.session_state.domain_data:
        cols = st.columns(3)
        for i, data in enumerate(st.session_state.domain_data):
            with cols[i % 3].expander(data["domain"]):
                outreach_subject = st.text_input(f"Subject for {data['domain']}", f"Backlink Opportunity for {data['domain']}", key=f"subject_{data['domain']}")
                outreach_email = st.text_area(f"Outreach Email for {data['domain']}", data["outreach_email"], height=200, key=f"outreach_email_{data['domain']}")
                selected_email = st.text_input(f"Email to send outreach for {data['domain']}", data["suggested_email"], key=f"selected_email_{data['domain']}")
                send_email = st.checkbox(f"Send Email for {data['domain']}", key=f"send_email_{data['domain']}")
                if send_email:
                    send_outreach_email(data, outreach_subject, outreach_email, selected_email)
    else:
        st.warning("⚠️ No domain data available. Please scrape some domains first.")

def send_outreach_email(domain_data, outreach_subject, outreach_email, selected_email):
    success_count = 0
    for smtp_config in st.session_state.smtp_configs:
        try:
            # Create a secure SMTP connection
            if smtp_config["port"] == 465:  # Port 465 is for SMTP with SSL
                smtp = smtplib.SMTP_SSL(smtp_config["server"], smtp_config["port"])
            else:  # Port 587 is for SMTP with TLS
                smtp = smtplib.SMTP(smtp_config["server"], smtp_config["port"])
                smtp.starttls()

            smtp.login(smtp_config["username"], smtp_config["password"])

            msg = MIMEText(outreach_email)
            msg['Subject'] = outreach_subject
            msg['From'] = smtp_config["sender_email"]
            msg['To'] = selected_email
            smtp.send_message(msg)
            success_count += 1

            smtp.quit()
            st.success(f"✅ Email sent successfully using SMTP configuration: {smtp_config['server']}, {smtp_config['username']}")
        except smtplib.SMTPAuthenticationError:
            st.warning(f"⚠️ Authentication failed for SMTP configuration: {smtp_config['server']}, {smtp_config['username']}")
        except Exception as e:
            st.error(f"❌ Error sending email with SMTP configuration {smtp_config['server']}, {smtp_config['username']}: {e}")

    if success_count > 0:
        st.success(f"✅ Email sent successfully!")

if st.button("🔍 Scrape Domains"):
    st.session_state.domain_data = scrape_domains(domains)

show_domain_data()
