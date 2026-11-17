"""
src/features/phishing_intent.py
Modular, explainable phishing-intent analysis engine.

Detects advanced social engineering patterns and deceitful intent that standard
lexical spam classifiers miss, including:
1. Business Email Compromise (BEC) & Executive Impersonation
2. Credential Theft & Account Lockout Lures
3. Payment, Invoice & Financial Fraud
4. Social Engineering, Authority Impersonation & Coercion
5. Malicious Document-Sharing & Cloud Lures

Outputs structured evidence, detected signal categories, risk tiers, and mitigating indicators.
"""

import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse


class PhishingIntentDetector:
    """
    Rule-based, explainable phishing intent analysis engine.
    Analyzes semantic combinations of authority claims, urgency, financial demands,
    credential requests, and link context without relying on brittle single-word triggers.
    """

    def __init__(self):
        # 1. BEC & Executive Impersonation Patterns
        self.executive_titles = re.compile(
            r"\b(ceo|chief\s+executive|cfo|chief\s+financial|coo|chief\s+operating|"
            r"president|managing\s+director|executive\s+director|founder|chairman|"
            r"board\s+of\s+directors|vice\s+president|general\s+counsel)\b",
            re.IGNORECASE
        )
        self.bec_secrecy_unavailable = re.compile(
            r"\b(keep\s+this\s+(confidential|private|between\s+us|strictly\s+confidential)|"
            r"(is|strictly)\s+confidential|treat\s+(this\s+)?with\s+confidentiality|"
            r"are\s+you\s+(at\s+your\s+desk|available|in\s+the\s+office)|"
            r"i\s+am\s+(currently\s+)?in\s+a\s+meeting|"
            r"cannot\s+(take|answer)\s+calls|do\s+not\s+call\s+me|"
            r"do\s+not\s+(verify\s+by\s+)?call(ing)?(\s+our)?|"
            r"do\s+not\s+involve\s+(finance|hr|accounting|anyone)|"
            r"(lines|phones?)\s+(are\s+being|are)\s+migrated|"
            r"text\s+me\s+at|handle\s+this\s+discreetly|need\s+a\s+quick\s+favor)\b",
            re.IGNORECASE
        )
        self.bec_gift_cards = re.compile(
            r"\b((buy|purchase|get)\s+(\d+\s+)?(some\s+)?([a-z]+\s+)?gift\s*cards?|"
            r"gift\s*cards?\s+(for\s+(our\s+)?(clients?|team|staff|incentive))|"
            r"scratch\s+(the\s+)?back\s+(and\s+send|off)|"
            r"send\s+(me\s+)?(the\s+codes?|photos?|pictures?)\s*(by\s+email|via\s+email|to\s+me)?)\b",
            re.IGNORECASE
        )
        self.bec_wire_transfer = re.compile(
            r"\b(wire\s+(transfer|funds?|money)|transfer\s+(the\s+)?funds?|(urgent|discreet|quick|confidential|acquisition)\s+wire|"
            r"(update[ds]?|change[ds]?|revised?)\s+(our\s+)?(settlement|banking|remittance|bank|vendor)\s+(account|details|instructions)?|"
            r"(new|revised)\s+(bank\s+account|routing\s+(number|code)|settlement\s+account)|"
            r"change\s+direct\s+deposit|"
            r"ignore\s+bank\s+details\s+on\s+previous|"
            r"remit\s+(all\s+)?(pending\s+)?(amounts?|funds?|payments?)|"
            r"process\s+an\s+urgent\s+(payment|wire))\b",
            re.IGNORECASE
        )

        # 2. Credential Theft & Account Verification Patterns
        self.cred_expiry_verify = re.compile(
            r"\b(password\s+(has\s+expired|expired|expires\s+(today|in\s+\d+\s+hours?|soon)|must\s+be\s+renewed)|"
            r"verify\s+your\s+(password|credentials|login|identity|account\s+access)|"
            r"confirm\s+your\s+(current\s+)?password|"
            r"(enter|reply\s+with|provide|send)\s+(your\s+)?(current\s+)?(username|password|credentials|recovery\s+phrase|current\s+authenticator\s+code)|"
            r"re-?authenticate\s+your\s+account|"
            r"identity\s+verification\s+required|"
            r"(recovery\s+phrase|authenticator\s+code))\b",
            re.IGNORECASE
        )
        self.cred_suspension_threat = re.compile(
            r"\b(account(\s+access)?\s+(will\s+be|has\s+been)\s+(suspended|locked|terminated|disabled|restricted|deactivated|closed)|"
            r"(temporarily\s+restricted\s+access|permanently\s+lock\s+(your\s+)?account)|"
            r"unauthorized\s+(security\s+)?(access|login|sign-?in)\s+detected|"
            r"suspicious\s+(activity|sign-?in|login)\s+detected|"
            r"security\s+breach\s+detected|"
            r"to\s+prevent\s+(immediate\s+)?(suspension|interruption|service\s+closure)|"
            r"ignoring\s+this\s+notice\s+may)\b",
            re.IGNORECASE
        )
        self.cred_action_link = re.compile(
            r"\b(click\s+(here\s+)?to\s+(verify|unlock|reactivate|confirm|restore|update|retain)|"
            r"log\s*in\s+to\s+(verify|update|unlock|confirm|review)|"
            r"sign\s*in\s+to\s+(verify|update|keep|restore|preview)|"
            r"(review|secure|unlock|restore|verify):\s*https?://|"
            r"verify\s+account\s+now|secure\s+your\s+account(\s+now)?)\b",
            re.IGNORECASE
        )

        # 3. Financial & Payment Fraud Patterns
        self.financial_invoice_scam = re.compile(
            r"\b((invoice|bill|statement)\s+#?[a-z0-9\-_]{4,}\b|"
            r"order\s+(confirmation|receipt|processed)|"
            r"you\s+have\s+been\s+charged\s+\$?\d+|"
            r"auto-?renewal\s+(of\s+\$?\d+|processed)|"
            r"subscription\s+(renewed|renewal\s+notice))\b",
            re.IGNORECASE
        )
        self.financial_cancel_lure = re.compile(
            r"\b(if\s+you\s+did\s+not\s+(make|authorize)\s+this\s+(purchase|charge|order)|"
            r"to\s+(cancel|dispute|refund)\s+(this\s+)?(order|subscription|charge)|"
            r"call\s+(us\s+immediately|our\s+(support|help\s*desk|billing\s+department))\s+at|"
            r"reach\s+(out\s+to\s+)?customer\s+support\s+to\s+cancel)\b",
            re.IGNORECASE
        )
        self.financial_refund_scam = re.compile(
            r"\b(refund\s+(approved|is\s+ready|credited|of\s+\$?\d+)|"
            r"claim\s+your\s+refund|accidental\s+(overcharge|payment))\b",
            re.IGNORECASE
        )
        self.financial_delivery_scam = re.compile(
            r"\b((package|parcel|shipment|delivery)\s+(failed|was\s+unsuccessful|could\s+not\s+be\s+delivered|could\s+not\s+be\s+validated|is\s+on\s+hold|at\s+the\s+terminal)|"
            r"attempted\s+delivery|"
            r"(redelivery\s+fee|unpaid\s+(customs|shipping|postal)\s+fee|fee\s+is\s+required)|"
            r"(package|parcel)\s+will\s+be\s+returned|"
            r"pay\s+(\$?\d+(\.\d{2})?|redelivery\s+fee)\s+to\s+(release|receive)|"
            r"update\s+delivery\s+address\s+and\s+pay)\b",
            re.IGNORECASE
        )

        # 4. Social Engineering, Impersonation & Coercion Patterns
        self.authority_impersonation = re.compile(
            r"\b(it\s+(help\s*desk|service\s*desk|support\s*team|administrator)|"
            r"mail\s*server\s*(administrator|team)|system\s*administrator|"
            r"microsoft\s*(365|security|support|team)|office\s*365\s*team|"
            r"google\s*workspace\s*admin|internal\s*revenue\s*service|\birs\b|"
            r"hmrc|security\s*operations\s*center|\bsoc\s*team\b|"
            r"human\s*resources\s*compliance|payroll\s*investigation)\b",
            re.IGNORECASE
        )
        self.severe_coercion = re.compile(
            r"\b(immediate\s+(legal\s+action|termination|arrest)|"
            r"within\s+\d+\s+hours|"
            r"failure\s+to\s+comply\s+will\s+result|"
            r"strictly\s+prohibited\s+from\s+sharing|"
            r"disciplinary\s+action\s+will\s+be\s+taken|"
            r"(request|link|code|session)\s+expires\s+in\s+\d+\s+minutes?)\b",
            re.IGNORECASE
        )
        self.sensitive_pii_demand = re.compile(
            r"\b(social\s+security\s+number|\bssn\b|driver'?s\s+license|"
            r"date\s+of\s+birth|\bdob\b|bank\s+account\s+number|"
            r"card\s+(details|number|security\s+code)|\bcvv\b|credit\s+card|"
            r"one-?time\s+(passcode|code)|\botp\b|2fa\s+code|(six|6)[\s\-]digit\s+sms\s+code)\b",
            re.IGNORECASE
        )

        # 5. Malicious Document-Sharing Patterns
        self.doc_sharing_lure = re.compile(
            r"\b((shared|sent)\s+a\s+(secure\s+)?(document|file|folder|pdf|spreadsheet|contract|agreement)\s+with\s+you|"
            r"(a\s+)?document\s+was\s+shared|"
            r"docusign\s+(envelope|document\s+ready\s+for\s+signature)|"
            r"onedrive\s+(shared\s+file|notification)|"
            r"sharepoint\s+(online\s+document|portal)|"
            r"review\s+attached\s+(contract|nda|invoice)|"
            r"view\s+encrypted\s+(message|email|document))\b",
            re.IGNORECASE
        )
        self.doc_login_demand = re.compile(
            r"\b(log\s*in\s+to\s+(view|download|decrypt|sign)|"
            r"sign\s*in\s+to\s+(preview|view|download)|"
            r"enter\s+your\s+(corporate\s+)?(email\s+)?password|"
            r"approve\s+the\s+authentication\s+notification|"
            r"sign\s*in\s+with\s+your\s+(work\s+)?email\s+credentials?|"
            r"authenticate\s+to\s+access\s+document)\b",
            re.IGNORECASE
        )

        # Mitigating & Benign Indicators (prevents false positives on legitimate notices)
        self.negative_security_advisory = re.compile(
            r"\b((will\s+never|never)\s+ask\s+(you\s+)?(for\s+your\s+)?(password|credentials?|one-?time\s+code|passcode|otp|pin|card\s+details|banking)|"
            r"never\s+(share|provide|disclose|send)\s+your\s+(password|credentials?|code|pin)|"
            r"payroll\s+will\s+never\s+ask|"
            r"use\s+your\s+(usual|saved)\s+(company\s+)?bookmark)\b",
            re.IGNORECASE
        )
        self.benign_security_phrasing = re.compile(
            r"\b(if\s+you\s+(recently\s+)?(made|requested)\s+this\s+change,?\s*(no\s+further\s+action\s+is\s+needed|no\s+action\s+is\s+(required|needed))|"
            r"if\s+this\s+was\s+you,?\s*(you\s+can\s+safely\s+ignore|no\s+action)|"
            r"this\s+is\s+an\s+automated\s+(notification|receipt|message)|"
            r"you\s+are\s+receiving\s+this\s+email\s+because\s+you\s+subscribed|"
            r"unsubscribe\s+from\s+this\s+list|manage\s+your\s+preferences)\b",
            re.IGNORECASE
        )
        self.benign_payroll_terms = re.compile(
            r"\b(direct\s+deposit\s+advice|payroll\s+schedule|paystub\s+is\s+now\s+available|"
            r"view\s+your\s+paystub\s+in\s+workday|standard\s+payroll\s+processing)\b",
            re.IGNORECASE
        )

        # Free Webmail Domains commonly abused for impersonation
        self.freemail_domains = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "aol.com", "icloud.com", "mail.com", "yandex.com", "proton.me", "protonmail.com"
        }

    def analyze(
        self,
        subject: str = "",
        body: str = "",
        sender: Optional[str] = None,
        extracted_urls: Optional[List[str]] = None,
        url_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates email content, sender identity, and link attributes to determine
        the presence and severity of deceptive phishing intent.
        """
        subject = subject or ""
        body = body or ""
        sender = sender or ""
        urls = extracted_urls or []
        combined_text = f"{subject}\n{body}"

        detected_categories: List[str] = []
        evidence: List[str] = []
        signals: List[str] = []
        mitigating_factors: List[str] = []

        raw_score = 0.0

        # Extract URL metadata
        has_phishing_url = False
        max_url_prob = 0.0
        if url_results:
            for ur in url_results:
                if ur.get("is_phishing"):
                    has_phishing_url = True
                p = ur.get("phishing_probability", 0.0)
                if p > max_url_prob:
                    max_url_prob = p

        # ---------------------------------------------------------------------
        # SENDER ANALYSIS
        # ---------------------------------------------------------------------
        sender_indicators = {
            "is_freemail": False,
            "display_name_impersonation": False,
            "sender_address": sender,
            "suspicious_sender_pattern": False,
        }

        sender_domain = ""
        sender_display_name = ""
        if "@" in sender:
            # Parse display name vs address
            match = re.search(r"^(.*?)(?:<([^>]+)>|([^\s@]+@[^\s@]+))", sender)
            if match:
                sender_display_name = (match.group(1) or "").strip().strip('"\'')
                addr = match.group(2) or match.group(3) or ""
                if "@" in addr:
                    sender_domain = addr.split("@")[-1].strip().lower()

            if sender_domain in self.freemail_domains:
                sender_indicators["is_freemail"] = True

            # If sender display name mentions executive or IT authority but uses freemail
            if sender_indicators["is_freemail"]:
                if self.executive_titles.search(sender_display_name):
                    sender_indicators["display_name_impersonation"] = True
                    signals.append("Executive Title with Free Webmail Address")
                    evidence.append(
                        f"Sender display name '{sender_display_name}' claims executive status but originates from free webmail provider ({sender_domain})."
                    )
                    detected_categories.append("BUSINESS_EMAIL_COMPROMISE")
                    raw_score += 35.0
                elif self.authority_impersonation.search(sender_display_name):
                    sender_indicators["display_name_impersonation"] = True
                    signals.append("Authority Name with Free Webmail Address")
                    evidence.append(
                        f"Sender display name '{sender_display_name}' claims organization authority but uses free webmail ({sender_domain})."
                    )
                    detected_categories.append("SOCIAL_ENGINEERING_IMPERSONATION")
                    raw_score += 35.0

        # ---------------------------------------------------------------------
        # 1. BUSINESS EMAIL COMPROMISE (BEC)
        # ---------------------------------------------------------------------
        has_exec_claim = bool(self.executive_titles.search(combined_text))
        has_secrecy = bool(self.bec_secrecy_unavailable.search(combined_text))
        has_gift_cards = bool(self.bec_gift_cards.search(combined_text))
        has_wire_transfer = bool(self.bec_wire_transfer.search(combined_text))

        if has_gift_cards:
            signals.append("Gift Card Purchase Demand")
            evidence.append("Solicits purchase of retail/app gift cards and request to send pin codes/photos.")
            detected_categories.append("BUSINESS_EMAIL_COMPROMISE")
            if has_exec_claim or has_secrecy or sender_indicators["display_name_impersonation"]:
                raw_score += 55.0
            else:
                raw_score += 40.0

        elif has_wire_transfer and (has_exec_claim or has_secrecy or sender_indicators["display_name_impersonation"]):
            signals.append("Executive Wire/Banking Redirection Request")
            evidence.append("Urgent wire transfer or vendor banking detail update associated with executive/confidential communication.")
            detected_categories.append("BUSINESS_EMAIL_COMPROMISE")
            raw_score += 55.0

        elif has_exec_claim and has_secrecy and len(urls) == 0:
            signals.append("Executive Availability Probing (Linkless BEC)")
            evidence.append("Probes employee availability from purported executive with instructions for confidentiality/call avoidance.")
            detected_categories.append("BUSINESS_EMAIL_COMPROMISE")
            raw_score += 35.0

        # ---------------------------------------------------------------------
        # 2. CREDENTIAL THEFT & ACCOUNT SECURITY LURES
        # ---------------------------------------------------------------------
        has_cred_expiry = bool(self.cred_expiry_verify.search(combined_text))
        has_suspension = bool(self.cred_suspension_threat.search(combined_text))
        has_action_link = bool(self.cred_action_link.search(combined_text))
        has_negative_advisory = bool(self.negative_security_advisory.search(combined_text))

        # Check for mitigating benign phrasing first (e.g. "if you made this change, no action needed")
        if self.benign_security_phrasing.search(combined_text):
            mitigating_factors.append("Contains standard benign notification notice ('if this was you, no action is needed')")

        if has_negative_advisory:
            mitigating_factors.append("Contains explicit security hygiene advice (credentials are never requested by email)")

        if (has_cred_expiry or (has_suspension and has_action_link)) and not (has_negative_advisory and len(urls) == 0):
            cred_weight = 0.0
            if has_cred_expiry:
                signals.append("Password Verification/Expiry Lure")
                evidence.append("Demands password entry, verification, or credential authentication.")
                cred_weight += 35.0

            if has_suspension:
                signals.append("Account Termination/Suspension Threat")
                evidence.append("Threatens account deactivation, termination, or unauthorized access penalty.")
                cred_weight += 25.0

            if has_action_link:
                signals.append("Urgent Verification Call-to-Action Link")
                evidence.append("Directs user to click immediate action link to prevent account lockout.")
                cred_weight += 20.0

            # Correlation with URLs
            if has_phishing_url:
                evidence.append("Credential verification lure correlates directly with a detected phishing destination URL.")
                cred_weight += 30.0
            elif len(urls) > 0:
                evidence.append("Contains call-to-action link accompanying credential request.")
                cred_weight += 15.0

            # Reduce if purely informational benign phrasing is present and no phishing URL
            if mitigating_factors and not has_phishing_url:
                cred_weight *= 0.4
                evidence.append("Informational phrasing detected without active credential capture link; risk adjusted downwards.")

            if cred_weight >= 30.0:
                detected_categories.append("CREDENTIAL_THEFT")
                raw_score += cred_weight

        # ---------------------------------------------------------------------
        # 3. PAYMENT & FINANCIAL FRAUD
        # ---------------------------------------------------------------------
        has_inv_scam = bool(self.financial_invoice_scam.search(combined_text))
        has_cancel_lure = bool(self.financial_cancel_lure.search(combined_text))
        has_refund = bool(self.financial_refund_scam.search(combined_text))
        has_delivery = bool(self.financial_delivery_scam.search(combined_text))

        if has_inv_scam and has_cancel_lure:
            signals.append("Fake Invoice with Cancellation/Call Lure")
            evidence.append("Presents an unexpected invoice or auto-renewal charge alongside urgent instructions to call/cancel if unauthorized.")
            detected_categories.append("FINANCIAL_FRAUD")
            raw_score += 45.0
        elif has_refund:
            signals.append("Spurious Refund Claim Lure")
            evidence.append("Announces an unsolicited refund, overcharge compensation, or rebate requiring claiming action.")
            detected_categories.append("FINANCIAL_FRAUD")
            raw_score += 40.0
        elif has_delivery:
            signals.append("Delivery Impound / Customs Fee Scam")
            evidence.append("Claims parcel held at depot due to unpaid customs/redelivery fee requiring payment.")
            detected_categories.append("FINANCIAL_FRAUD")
            raw_score += 45.0

        # ---------------------------------------------------------------------
        # 4. SOCIAL ENGINEERING & IMPERSONATION
        # ---------------------------------------------------------------------
        has_auth_imp = bool(self.authority_impersonation.search(combined_text))
        has_coercion = bool(self.severe_coercion.search(combined_text))
        has_pii = bool(self.sensitive_pii_demand.search(combined_text))

        if has_pii:
            if has_negative_advisory and len(urls) == 0:
                mitigating_factors.append("Credential terms appear in educational warning context without external link capture")
            else:
                signals.append("Sensitive PII / Credential Demand")
                evidence.append("Directly asks for sensitive data (SSN, 2FA code, OTP, banking identification, or card details).")
                detected_categories.append("SOCIAL_ENGINEERING_IMPERSONATION")
                raw_score += 50.0

        if has_auth_imp and has_coercion:
            signals.append("Authority Impersonation with Coercive Deadline")
            evidence.append("Impersonates IT, administrative, or tax authority combined with strict disciplinary/legal deadline.")
            detected_categories.append("SOCIAL_ENGINEERING_IMPERSONATION")
            raw_score += 45.0
        elif has_auth_imp and (has_cred_expiry or has_action_link):
            signals.append("IT / Administrative Support Impersonation")
            evidence.append("Impersonates internal IT or system administrator requesting security action.")
            detected_categories.append("SOCIAL_ENGINEERING_IMPERSONATION")
            raw_score += 35.0

        # ---------------------------------------------------------------------
        # 5. MALICIOUS DOCUMENT-SHARING LURES
        # ---------------------------------------------------------------------
        has_doc_lure = bool(self.doc_sharing_lure.search(combined_text))
        has_doc_login = bool(self.doc_login_demand.search(combined_text))

        if has_doc_lure and (has_doc_login or has_phishing_url):
            signals.append("Deceptive Cloud Document Sharing Lure")
            evidence.append("Purports to share a secure document/contract requiring immediate login or linking to suspicious domain.")
            detected_categories.append("MALICIOUS_DOCUMENT_LURE")
            raw_score += 45.0

        # ---------------------------------------------------------------------
        # MITIGATING BENIGN FACTORS
        # ---------------------------------------------------------------------
        if self.benign_payroll_terms.search(combined_text) and not (has_gift_cards or has_wire_transfer or has_phishing_url):
            mitigating_factors.append("Standard legitimate payroll schedule/paystub distribution wording")
            raw_score = max(0.0, raw_score - 30.0)

        # ---------------------------------------------------------------------
        # SYNTHESIS & RISK LEVEL DETERMINATION
        # ---------------------------------------------------------------------
        intent_score = min(100.0, round(raw_score, 1))

        # Risk Tiering
        if intent_score >= 50.0 or has_gift_cards or (has_cred_expiry and (has_phishing_url or len(urls) > 0)):
            intent_risk_level = "HIGH"
            has_phishing_intent = True
        elif intent_score >= 30.0 or (len(detected_categories) > 0 and len(signals) >= 2):
            intent_risk_level = "MEDIUM"
            has_phishing_intent = True
        elif intent_score >= 15.0 or len(detected_categories) > 0:
            intent_risk_level = "LOW"
            has_phishing_intent = True
        else:
            intent_risk_level = "NONE"
            has_phishing_intent = False

        # Determine Primary Intent
        if "BUSINESS_EMAIL_COMPROMISE" in detected_categories:
            primary_intent = "BUSINESS_EMAIL_COMPROMISE"
        elif "CREDENTIAL_THEFT" in detected_categories:
            primary_intent = "CREDENTIAL_THEFT"
        elif "FINANCIAL_FRAUD" in detected_categories:
            primary_intent = "FINANCIAL_FRAUD"
        elif "MALICIOUS_DOCUMENT_LURE" in detected_categories:
            primary_intent = "MALICIOUS_DOCUMENT_LURE"
        elif "SOCIAL_ENGINEERING_IMPERSONATION" in detected_categories:
            primary_intent = "SOCIAL_ENGINEERING_IMPERSONATION"
        elif len(detected_categories) > 0:
            primary_intent = detected_categories[0]
        else:
            primary_intent = "NONE"

        return {
            "has_phishing_intent": has_phishing_intent,
            "primary_intent": primary_intent,
            "intent_categories_detected": list(set(detected_categories)),
            "intent_risk_level": intent_risk_level,
            "intent_score": intent_score,
            "detected_signals": signals,
            "evidence": evidence,
            "sender_indicators": sender_indicators,
            "mitigating_factors": mitigating_factors,
        }
