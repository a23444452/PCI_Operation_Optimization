from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5433/pci_optimization"

    # JWT
    jwt_secret: str = "change-me"
    jwt_expiry_hours: int = 8
    jwt_refresh_expiry_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:8080"

    # Azure AD
    azure_ad_client_id: str = ""
    azure_ad_tenant_id: str = ""
    ad_required_group: str = "PCI-Optimization-Access"

    # LDAP
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""

    # SMTP (Corning internal: smtphub.corning.com:25, no auth needed)
    smtp_host: str = ""
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_sender: str = "PCIHermes@corning.com"

    # Admin notification
    admin_notification_emails: str = ""
    app_base_url: str = "http://localhost:8080"

    # External data sources
    ppda_conn: str = ""  # Oracle connection string for PPDA
    mesdw_conn: str = ""  # MSSQL connection string for MESDW
    cube_conn: str = ""  # SSAS cube connection string
    adomd_dll_path: str = ""  # Path to Microsoft.AnalysisServices.AdomdClient.dll

    # Shipping
    shipping_folder: str = ""  # Shared folder path for shipping data

    # ETL
    etl_enabled: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
