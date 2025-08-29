class Config:
    # Flask-Session configuration
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"
    
    # Email configuration
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_SENDER = "donotreply.volunteer.org@gmail.com"
    EMAIL_PASSWORD = "oqek ztdx cvdh vxhw"  # Note: In production, use environment variables
    
    # Database configuration
    DATABASE_PATH = 'volunteer.db'
    
    # US States list
    STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY",
              "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
              "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
    