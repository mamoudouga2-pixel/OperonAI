from __future__ import annotations

ERROR_MESSAGES = {
    "SYS_UNSUPPORTED_PLATFORM": "এই কম্পিউটারটি সমর্থিত নয়।",
    "SYS_INSUFFICIENT_MEMORY": "এই কাজের জন্য পর্যাপ্ত মেমোরি নেই।",
    "SYS_INSUFFICIENT_STORAGE": "এই উপাদানটি ইনস্টল করতে আরও খালি জায়গা প্রয়োজন।",
    "SYS_PERMISSION_DENIED": "প্রয়োজনীয় অনুমতি দেওয়া হয়নি।",
    "DL_NETWORK_FAILED": "ডাউনলোডের সময় নেটওয়ার্ক সমস্যা হয়েছে।",
    "DL_TIMEOUT": "ডাউনলোডের সময়সীমা শেষ হয়েছে।",
    "DL_RESUME_FAILED": "আগের ডাউনলোড নিরাপদভাবে পুনরায় চালু করা যায়নি।",
    "DL_SOURCE_UNAVAILABLE": "প্রয়োজনীয় ডাউনলোড উৎসে পৌঁছানো যায়নি।",
    "DL_SIZE_MISMATCH": "ডাউনলোড করা ফাইলের আকার মেলেনি।",
    "SEC_MANIFEST_INVALID": "ইনস্টলেশন ম্যানিফেস্টটি বৈধ নয়।",
    "SEC_SIGNATURE_INVALID": "ডাউনলোড করা উপাদানটির নিরাপত্তা যাচাই সফল হয়নি।",
    "SEC_CHECKSUM_MISMATCH": "ডাউনলোড করা উপাদানটি অখণ্ড নয়।",
    "SEC_UNTRUSTED_SOURCE": "ডাউনলোড উৎসটি বিশ্বস্ত নয়।",
    "SEC_ARCHIVE_PATH_TRAVERSAL": "আর্কাইভে অনিরাপদ ফাইল পাথ পাওয়া গেছে।",
    "INS_DEPENDENCY_CONFLICT": "উপাদানগুলোর মধ্যে version conflict পাওয়া গেছে।",
    "INS_COMPONENT_FAILED": "উপাদানটি ইনস্টল করা যায়নি।",
    "INS_CONFIGURATION_FAILED": "উপাদান কনফিগার করা যায়নি।",
    "INS_ACTIVATION_FAILED": "উপাদানটি সক্রিয় করা যায়নি।",
    "RUN_INSTALL_FAILED": "স্থানীয় runtime ইনস্টল করা যায়নি।",
    "RUN_START_FAILED": "স্থানীয় runtime চালু করা যায়নি।",
    "RUN_HEALTH_FAILED": "স্থানীয় runtime স্বাস্থ্য পরীক্ষায় ব্যর্থ হয়েছে।",
    "RUN_VERSION_INCOMPATIBLE": "স্থানীয় runtime-এর version সমর্থিত নয়।",
    "UPD_MANIFEST_INVALID": "আপডেট ম্যানিফেস্ট অবৈধ।",
    "UPD_INCOMPATIBLE": "এই আপডেটটি বর্তমান সংস্করণের সঙ্গে সামঞ্জস্যপূর্ণ নয়।",
    "UPD_MIGRATION_FAILED": "ডেটা migration ব্যর্থ হয়েছে।",
    "UPD_HEALTH_FAILED": "আপডেটের পর স্বাস্থ্য পরীক্ষা ব্যর্থ হয়েছে।",
    "UPD_ROLLBACK_FAILED": "আগের কার্যকর সংস্করণে ফিরে যাওয়া যায়নি।",
    "REP_SCAN_FAILED": "ইনস্টলেশন পরীক্ষা করা যায়নি।",
    "REP_ARTIFACT_UNAVAILABLE": "repair-এর প্রয়োজনীয় উপাদান পাওয়া যায়নি।",
    "REP_REPAIR_FAILED": "উপাদানটি repair করা যায়নি।",
}

class InstallerError(Exception):
    def __init__(self, message: str, code: str = "INSTALLER_ERROR", *, details=None):
        super().__init__(message); self.code=code; self.details=details or {}
class ManifestError(InstallerError): pass
class VerificationError(InstallerError): pass
class DownloadError(InstallerError): pass
class DependencyConflict(InstallerError): pass
class StateError(InstallerError): pass
class InstallationError(InstallerError): pass
class PermissionDenied(InstallerError): pass

def user_message(code: str) -> str:
    return ERROR_MESSAGES.get(code, "একটি সমস্যা হয়েছে। বিস্তারিত তথ্য লগে রাখা হয়েছে।")
