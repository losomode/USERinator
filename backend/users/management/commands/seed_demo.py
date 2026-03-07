"""
Seed demo data for USERinator.

Creates companies and user profiles with role assignments.
Idempotent — safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from companies.models import Company
from users.models import UserProfile
from roles.models import Role
from permissions import PermissionChecker

# Role level constants
ROLE_ADMIN = 100
ROLE_MANAGER = 30
ROLE_MEMBER = 10

COMPANIES = [
    {
        'id': 1,
        'name': 'Acme Corporation',
        'address': '123 Tech Drive, Silicon Valley, CA 94025',
        'phone': '555-0100',
        'website': 'https://acme.example.com',
        'industry': 'Technology',
        'company_size': '1000+',
        'logo_url': '',
        'billing_contact_email': 'billing@acme.example.com',
        'custom_fields': {},
        'tags': ['enterprise', 'technology'],
        'notes': 'Large technology company with full RBAC hierarchy',
        'account_status': 'ACTIVE',
    },
    {
        'id': 2,
        'name': 'Globex Industries',
        'address': '456 Industrial Blvd, Detroit, MI 48201',
        'phone': '555-0200',
        'website': 'https://globex.example.com',
        'industry': 'Manufacturing',
        'company_size': '500-1000',
        'logo_url': '',
        'billing_contact_email': 'billing@globex.example.com',
        'custom_fields': {},
        'tags': ['manufacturing', 'mid-size'],
        'notes': 'Mid-size manufacturing company',
        'account_status': 'ACTIVE',
    },
    {
        'id': 3,
        'name': 'Initech LLC',
        'address': '789 Software Lane, Austin, TX 78701',
        'phone': '555-0300',
        'website': 'https://initech.example.com',
        'industry': 'Software',
        'company_size': '50-100',
        'logo_url': '',
        'billing_contact_email': 'billing@initech.example.com',
        'custom_fields': {},
        'tags': ['software', 'small-business'],
        'notes': 'Small software development company',
        'account_status': 'ACTIVE',
    },
    {
        'id': 4,
        'name': 'Wayne Enterprises',
        'address': '1007 Mountain Drive, Gotham, NJ 07001',
        'phone': '555-0400',
        'website': 'https://wayne.example.com',
        'industry': 'Technology/Security',
        'company_size': '1000+',
        'logo_url': '',
        'billing_contact_email': 'billing@wayne.example.com',
        'custom_fields': {},
        'tags': ['enterprise', 'security', 'technology'],
        'notes': 'Large enterprise with diverse technology and security products',
        'account_status': 'ACTIVE',
    },
]

USER_PROFILES = [
    # Platform Admins (no company)
    {'user_id': 1, 'username': 'admin', 'email': 'admin@example.com', 
     'display_name': 'Admin User', 'role_name': 'ADMIN', 'role_level': ROLE_ADMIN, 'company_id': None},
    {'user_id': 2, 'username': 'alice.admin', 'email': 'alice@example.com', 
     'display_name': 'Alice Admin', 'role_name': 'ADMIN', 'role_level': ROLE_ADMIN, 'company_id': None},
    
    # Acme Corporation
    {'user_id': 101, 'username': 'bob.manager', 'email': 'bob@acme.example.com', 
     'display_name': 'Bob Manager', 'role_name': 'MANAGER', 'role_level': ROLE_MANAGER, 'company_id': 1,
     'job_title': 'Operations Manager', 'department': 'Operations'},
    {'user_id': 102, 'username': 'carol.member', 'email': 'carol@acme.example.com', 
     'display_name': 'Carol Member', 'role_name': 'MEMBER', 'role_level': ROLE_MEMBER, 'company_id': 1,
     'job_title': 'Support Specialist', 'department': 'Support'},
    {'user_id': 103, 'username': 'dave.member', 'email': 'dave@acme.example.com', 
     'display_name': 'Dave Member', 'role_name': 'MEMBER', 'role_level': ROLE_MEMBER, 'company_id': 1,
     'job_title': 'Sales Representative', 'department': 'Sales'},
    
    # Globex Industries
    {'user_id': 104, 'username': 'frank.manager', 'email': 'frank@globex.example.com', 
     'display_name': 'Frank Manager', 'role_name': 'MANAGER', 'role_level': ROLE_MANAGER, 'company_id': 2,
     'job_title': 'Plant Manager', 'department': 'Operations'},
    {'user_id': 105, 'username': 'grace.member', 'email': 'grace@globex.example.com', 
     'display_name': 'Grace Member', 'role_name': 'MEMBER', 'role_level': ROLE_MEMBER, 'company_id': 2,
     'job_title': 'Quality Inspector', 'department': 'Quality'},
    
    # Initech LLC
    {'user_id': 106, 'username': 'henry.manager', 'email': 'henry@initech.example.com', 
     'display_name': 'Henry Manager', 'role_name': 'MANAGER', 'role_level': ROLE_MANAGER, 'company_id': 3,
     'job_title': 'Engineering Manager', 'department': 'Engineering'},
    {'user_id': 107, 'username': 'iris.member', 'email': 'iris@initech.example.com', 
     'display_name': 'Iris Member', 'role_name': 'MEMBER', 'role_level': ROLE_MEMBER, 'company_id': 3,
     'job_title': 'Software Developer', 'department': 'Engineering'},
    
    # Wayne Enterprises
    {'user_id': 108, 'username': 'jack.manager', 'email': 'jack@wayne.example.com', 
     'display_name': 'Jack Manager', 'role_name': 'MANAGER', 'role_level': ROLE_MANAGER, 'company_id': 4,
     'job_title': 'Security Manager', 'department': 'Security'},
    {'user_id': 109, 'username': 'kate.member', 'email': 'kate@wayne.example.com', 
     'display_name': 'Kate Member', 'role_name': 'MEMBER', 'role_level': ROLE_MEMBER, 'company_id': 4,
     'job_title': 'Security Analyst', 'department': 'Security'},
    {'user_id': 110, 'username': 'leo.member', 'email': 'leo@wayne.example.com', 
     'display_name': 'Leo Member', 'role_name': 'MEMBER', 'role_level': ROLE_MEMBER, 'company_id': 4,
     'job_title': 'Field Technician', 'department': 'Operations'},
]


class Command(BaseCommand):
    help = 'Seed demo data for USERinator - companies and user profiles'

    def handle(self, *args, **options):
        self.stdout.write('👥 Seeding USERinator demo data...')

        # Create system roles
        self.stdout.write('  Creating system roles...')
        roles_data = [
            {'role_name': 'ADMIN', 'role_level': ROLE_ADMIN, 'description': 'Platform administrator with full access', 'is_system_role': True},
            {'role_name': 'MANAGER', 'role_level': ROLE_MANAGER, 'description': 'Company manager with elevated permissions', 'is_system_role': True},
            {'role_name': 'MEMBER', 'role_level': ROLE_MEMBER, 'description': 'Standard company member', 'is_system_role': True},
        ]
        for role_data in roles_data:
            role, created = Role.objects.update_or_create(
                role_name=role_data['role_name'],
                defaults=role_data
            )
            if created:
                self.stdout.write(f'    ✓ {role.role_name} (level {role.role_level}) - created')
            else:
                self.stdout.write(f'    ✓ {role.role_name} (level {role.role_level}) - updated')

        # Create companies
        self.stdout.write('  Creating companies...')
        for company_data in COMPANIES:
            company, created = Company.objects.update_or_create(
                id=company_data['id'],
                defaults=company_data
            )
            if created:
                self.stdout.write(f'    ✓ {company.name} (created)')
            else:
                self.stdout.write(f'    ✓ {company.name} (updated)')

        # Create user profiles
        self.stdout.write('  Creating user profiles...')
        for profile_data in USER_PROFILES:
            # Get company if specified
            company = None
            if profile_data.get('company_id'):
                try:
                    company = Company.objects.get(id=profile_data['company_id'])
                except Company.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"    ! Company {profile_data['company_id']} not found for {profile_data['username']}"
                    ))
                    continue
            
            # Prepare profile data
            profile_defaults = {
                'username': profile_data['username'],
                'email': profile_data['email'],
                'display_name': profile_data['display_name'],
                'role_name': profile_data['role_name'],
                'role_level': profile_data['role_level'],
                'company': company,
                'job_title': profile_data.get('job_title', ''),
                'department': profile_data.get('department', ''),
                'is_active': True,
            }
            
            profile, created = UserProfile.objects.update_or_create(
                user_id=profile_data['user_id'],
                defaults=profile_defaults
            )
            
            role_display = profile_data['role_name']
            company_display = company.name if company else 'Platform'
            if created:
                self.stdout.write(f'    ✓ {profile.display_name} - {role_display} @ {company_display} (created)')
            else:
                self.stdout.write(f'    ✓ {profile.display_name} - {role_display} @ {company_display} (updated)')

        self.stdout.write(self.style.SUCCESS('✅ USERinator: 4 companies, 12 users seeded'))
        self.stdout.write('   Role levels: ADMIN=100, MANAGER=30, MEMBER=10')
