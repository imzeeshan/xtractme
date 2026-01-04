# Django Admin User Setup

## Current Admin Users

You already have an admin user configured:
- **Username**: admin
- **Email**: admin@example.com

## Access Admin Panel

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to: http://localhost:8000/admin/

3. Login with your admin credentials

## Create a New Admin User

### Option 1: Using the Simple Script (Non-Interactive)

```bash
python create_admin_simple.py <username> <password> <email>
```

Example:
```bash
python create_admin_simple.py myadmin mypassword123 myadmin@example.com
```

### Option 2: Using Django's Interactive Command (Recommended)

```bash
python manage.py createsuperuser
```

This will prompt you for:
- Username
- Email (optional)
- Password (entered twice for confirmation)

### Option 3: Using the Interactive Script

```bash
python create_admin.py
```

This script will guide you through creating an admin user interactively.

## Reset Admin Password

If you need to reset an existing admin user's password:

### Method 1: Using Django Shell

```bash
python manage.py shell
```

Then run:
```python
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='admin')
user.set_password('newpassword123')
user.save()
exit()
```

### Method 2: Using the Simple Script

```bash
python create_admin_simple.py admin newpassword123 admin@example.com
```

This will update the existing user's password.

## List All Admin Users

To see all superusers:

```bash
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); [print(f'{u.username} - {u.email}') for u in User.objects.filter(is_superuser=True)]"
```

## Security Notes

⚠️ **Important**: 
- Change default passwords before deploying to production
- Use strong passwords
- Never commit admin credentials to version control
- Consider using environment variables for sensitive data

## Default Credentials (Development Only)

If you used the simple script with defaults:
- **Username**: admin
- **Password**: admin123
- **Email**: admin@example.com

**⚠️ Change these before production deployment!**

