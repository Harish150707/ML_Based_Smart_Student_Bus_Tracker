import os


def get_mail_config():
	return {
		"MAIL_SERVER": os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
		"MAIL_PORT": int(os.environ.get("MAIL_PORT", "587")),
		"MAIL_USE_TLS": os.environ.get("MAIL_USE_TLS", "true").lower() == "true",
		"MAIL_USERNAME": os.environ.get("MAIL_USERNAME", ""),
		"MAIL_PASSWORD": os.environ.get("MAIL_PASSWORD", ""),
	}
