# PART 09 — SECURITY SYSTEM — FIX LOG (v1.1)

মূল zip (`PART09_SECURITY_PERMISSION_SAFETY_COMPLETE.zip`) কম্পাইল হচ্ছিল এবং ১৪টি পুরনো টেস্ট পাস করছিল, কিন্তু স্পেসিফিকেশন (DOCX, বিশেষত ধারা 9.20, 9.24, 9.13, 9.14) এর সাথে মিলিয়ে দেখার পর নিচের ফাঁক/বাগগুলো পাওয়া গেছে এবং ঠিক করা হয়েছে।

## যা প্রকৃত বাগ ছিল

1. **`audit/integrity.py` — Audit integrity আসলে কিছুই যাচাই করত না।**
   আগের কোড হ্যাশ চেইন হিসাব করত কিন্তু কোথাও রাখত/তুলনা করত না — সবসময় `True` রিটার্ন করত, log tamper হলেও ধরা পড়ত না। এটা স্পেসিফিকেশনের 9.20 (Audit Integrity / tamper-evidence) ধারার সরাসরি লঙ্ঘন।
   **ফিক্স:** `audit/logger.py` এখন প্রতিটি রেকর্ডে `prev_hash`/`hash` জমা রাখে (real hash chain)। `audit/integrity.py` এখন চেইন পুনর্গণনা করে প্রতিটি রেকর্ডের সংরক্ষিত হ্যাশের সাথে মেলায়; কোনো রেকর্ড বদলানো, বাদ দেওয়া বা ক্রম পরিবর্তন হলে `False` রিটার্ন করে।

## যা স্পেসিফিকেশনে ছিল কিন্তু implement/wire করা হয়নি

2. **Approval expiry** — `APPROVAL_EXPIRED` status/event কখনো সেট হতো না; `ApprovalManager.matches()` চুপচাপ `False` দিত। এখন expire হওয়া approval-এর status `EXPIRED`-এ বদলায় এবং audit-এ `APPROVAL_EXPIRED` event যায়।
3. **9.24-এর ইভেন্ট তালিকা বাস্তবে trigger হতো না** — `APPROVAL_GRANTED`, `APPROVAL_REJECTED`, `APPROVAL_EXPIRED`, `CREDENTIAL_ACCESS_BLOCKED`, `RATE_LIMIT_EXCEEDED`, `SECURITY_INCIDENT_DETECTED` — এই ছয়টা event কোথাও log হচ্ছিল না। এখন `ApprovalManager`, `Vault`, `RateLimiter`, `IncidentResponse` — সবগুলোতে ঐচ্ছিক `audit` hook যোগ করা হয়েছে যা এই event গুলো log করে (backward-compatible, `audit=None` default)।
4. **Network policy — size/duration limit চেক হতো না** (স্পেস 9.13: "Download size/time limits")। `NetworkPolicy`/`NetworkRequestGuard`-এ `max_size` এবং নতুন `max_duration` চেক যোগ করা হয়েছে।
5. **`credentials/vault.py`** স্পেসিফিকেশনের `CredentialProvider` interface বাস্তবায়ন করছিল না (আলাদা ক্লাস, কোনো সম্পর্ক ছিল না)। এখন `Vault(CredentialProvider)`।
6. **`incident/response.py`** শুধু একটা static dict রিটার্ন করত, Core-কে কোনো audit trail ছাড়া। এখন `respond(action, audit)` কল করলে `SECURITY_INCIDENT_DETECTED` audit-এ log হয়।

## টেস্ট কভারেজ বাড়ানো হয়েছে (9.26 প্রতিটি আইটেমের জন্য)

আগে ১৪টা টেস্ট ছিল, এখন **২৩টা**, নতুনগুলো:
- `test_audit_tamper_detected`, `test_audit_missing_record_detected` — audit integrity সত্যিকারের tamper ধরে কিনা
- `test_symlink_escape` — allowed root-এর বাইরে symlink দিয়ে escape করার চেষ্টা block হয় কিনা
- `test_approval_expiry` — মেয়াদ শেষ হওয়া approval আর valid থাকে না + event log হয়
- `test_credential_access_blocked_is_audited_and_redacted` — অননুমোদিত credential access audit-এ log হয় এবং log-এ plaintext secret থাকে না
- `test_plugin_undeclared_capability_denied_via_guard` — ঘোষণা না করা capability পুরো guard pipeline দিয়ে deny হয়
- `test_network_redirect_and_size_limits` — redirect/size/duration limit ছাড়ালে network request deny হয়
- `test_rate_limit_is_audited` — rate limit ছাড়ালে `RATE_LIMIT_EXCEEDED` audit event তৈরি হয়
- `test_incident_response_notifies_and_audits` — incident detect + response + audit trail

## ফলাফল

```
COMPILE_RETURN=0
TEST_RETURN=0
Ran 23 tests ... OK
```

সব change **backward-compatible** — নতুন প্যারামিটারগুলো (`audit=`, `rate_limiter=`, `max_duration=`) সবই optional এবং default `None`/আগের ডিফল্ট মান, তাই অন্য Part (04/05/06/07/08/10) যেভাবে এই module import করছে তা ভাঙবে না।
