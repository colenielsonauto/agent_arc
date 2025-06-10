#!/usr/bin/env python3
"""
Interactive CLI onboarding wizard for new email router clients.
🧙‍♂️ Guides users through creating client configurations with validation.
"""

import os
import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.domain_resolver import normalize_domain, is_valid_domain_format
from app.models.client_config import ClientConfig


class Colors:
    """ANSI color codes for pretty CLI output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ClientOnboardingWizard:
    """
    Interactive wizard for onboarding new email router clients.
    
    Guides users through:
    1. Basic client information
    2. Domain configuration
    3. Email routing setup
    4. Branding customization
    5. Configuration validation
    """
    
    def __init__(self):
        """Initialize the onboarding wizard."""
        self.client_data = {}
        self.clients_dir = Path("clients/active")
        self.templates_dir = Path("clients/templates/default")
        
        # Ensure directories exist
        self.clients_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self):
        """Run the complete onboarding wizard."""
        self._print_header()
        
        try:
            # Step 1: Basic client information
            self._collect_basic_info()
            
            # Step 2: Domain configuration
            self._collect_domain_config()
            
            # Step 3: Contact information
            self._collect_contact_info()
            
            # Step 4: Email routing setup
            self._collect_routing_config()
            
            # Step 5: Branding customization
            self._collect_branding_config()
            
            # Step 6: Settings configuration
            self._collect_settings_config()
            
            # Step 7: Generate configuration files
            self._generate_config_files()
            
            # Step 8: Validate configuration
            self._validate_configuration()
            
            self._print_success()
            
        except KeyboardInterrupt:
            self._print_error("Onboarding cancelled by user.")
            sys.exit(1)
        except Exception as e:
            self._print_error(f"Onboarding failed: {e}")
            sys.exit(1)
    
    def _print_header(self):
        """Print wizard header."""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                 📧 EMAIL ROUTER ONBOARDING                  ║")
        print("║              Multi-Tenant Client Setup Wizard               ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Welcome! This wizard will help you set up a new client for the email router.{Colors.ENDC}")
        print()
    
    def _print_success(self):
        """Print success message."""
        client_id = self.client_data['client']['id']
        print(f"{Colors.OKGREEN}{Colors.BOLD}")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                    ✅ SETUP COMPLETE!                       ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Client '{client_id}' has been successfully configured!{Colors.ENDC}")
        print()
        print(f"{Colors.OKBLUE}Configuration files created:{Colors.ENDC}")
        print(f"  • clients/active/{client_id}/client-config.yaml")
        print(f"  • clients/active/{client_id}/routing-rules.yaml")
        print()
        print(f"{Colors.OKBLUE}Next steps:{Colors.ENDC}")
        print("  1. Review the generated configuration files")
        print("  2. Customize AI prompts in the ai-context/ directory if needed")
        print("  3. Test the configuration with a webhook call")
        print("  4. Set up DNS records for email routing")
        print()
    
    def _print_error(self, message: str):
        """Print error message."""
        print(f"{Colors.FAIL}❌ Error: {message}{Colors.ENDC}")
    
    def _print_warning(self, message: str):
        """Print warning message."""
        print(f"{Colors.WARNING}⚠️  Warning: {message}{Colors.ENDC}")
    
    def _print_info(self, message: str):
        """Print info message."""
        print(f"{Colors.OKBLUE}ℹ️  {message}{Colors.ENDC}")
    
    def _prompt(self, question: str, default: str = None, validator=None) -> str:
        """
        Prompt user for input with validation.
        
        Args:
            question: Question to ask
            default: Default value if empty input
            validator: Function to validate input
            
        Returns:
            Validated user input
        """
        while True:
            if default:
                prompt = f"{question} [{default}]: "
            else:
                prompt = f"{question}: "
            
            response = input(prompt).strip()
            
            if not response and default:
                response = default
            
            if not response:
                self._print_error("Please provide a value.")
                continue
            
            if validator:
                is_valid, error_message = validator(response)
                if not is_valid:
                    self._print_error(error_message)
                    continue
            
            return response
    
    def _prompt_choice(self, question: str, choices: List[str], default: str = None) -> str:
        """Prompt user to choose from a list of options."""
        print(f"{question}")
        for i, choice in enumerate(choices, 1):
            marker = " (default)" if choice == default else ""
            print(f"  {i}. {choice}{marker}")
        
        while True:
            try:
                if default:
                    prompt = f"Choose [1-{len(choices)}] [default: {choices.index(default) + 1}]: "
                else:
                    prompt = f"Choose [1-{len(choices)}]: "
                
                response = input(prompt).strip()
                
                if not response and default:
                    return default
                
                choice_num = int(response)
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1]
                else:
                    self._print_error(f"Please choose a number between 1 and {len(choices)}.")
            except ValueError:
                self._print_error("Please enter a valid number.")
    
    def _validate_client_id(self, client_id: str) -> tuple[bool, str]:
        """Validate client ID format."""
        if not client_id.startswith('client-'):
            return False, "Client ID must start with 'client-'"
        
        if not re.match(r'^client-\d{3}-[a-zA-Z0-9-]+$', client_id):
            return False, "Client ID format should be 'client-XXX-company-name' (e.g., 'client-001-acme-corp')"
        
        # Check if client already exists
        client_dir = self.clients_dir / client_id
        if client_dir.exists():
            return False, f"Client '{client_id}' already exists"
        
        return True, ""
    
    def _validate_email(self, email: str) -> tuple[bool, str]:
        """Validate email address format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email address format"
        return True, ""
    
    def _validate_domain(self, domain: str) -> tuple[bool, str]:
        """Validate domain format."""
        normalized = normalize_domain(domain)
        if not normalized:
            return False, "Invalid domain format"
        
        if not is_valid_domain_format(normalized):
            return False, "Domain contains invalid characters"
        
        return True, ""
    
    def _validate_hex_color(self, color: str) -> tuple[bool, str]:
        """Validate hex color format."""
        if not color.startswith('#'):
            color = f"#{color}"
        
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            return False, "Color must be a valid hex color (e.g., #667eea)"
        
        return True, ""
    
    def _collect_basic_info(self):
        """Collect basic client information."""
        print(f"{Colors.BOLD}Step 1: Basic Information{Colors.ENDC}")
        print("─" * 50)
        
        # Client ID
        self._print_info("Client ID should follow the format: client-XXX-company-name")
        self._print_info("Example: client-001-acme-corp")
        client_id = self._prompt(
            "Client ID",
            validator=self._validate_client_id
        )
        
        # Company name
        company_name = self._prompt("Company/Organization Name")
        
        # Industry
        industries = [
            "Technology", "Healthcare", "Finance", "Retail", "Manufacturing",
            "Education", "Government", "Non-profit", "Legal", "Other"
        ]
        industry = self._prompt_choice("Industry", industries, "Technology")
        
        # Timezone
        timezones = [
            "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
            "Europe/London", "Europe/Paris", "Asia/Tokyo", "Australia/Sydney"
        ]
        timezone = self._prompt_choice("Timezone", timezones, "UTC")
        
        # Business hours
        business_hours = self._prompt("Business hours (e.g., 9-17)", "9-17")
        
        self.client_data['client'] = {
            'id': client_id,
            'name': company_name,
            'industry': industry,
            'status': 'active',
            'timezone': timezone,
            'business_hours': business_hours
        }
        
        print(f"{Colors.OKGREEN}✓ Basic information collected{Colors.ENDC}")
        print()
    
    def _collect_domain_config(self):
        """Collect domain configuration."""
        print(f"{Colors.BOLD}Step 2: Domain Configuration{Colors.ENDC}")
        print("─" * 50)
        
        # Primary domain
        self._print_info("This is the main domain for your organization")
        primary_domain = self._prompt(
            "Primary domain (e.g., company.com)",
            validator=self._validate_domain
        )
        
        # Support domain (can be different)
        self._print_info("Email address where support emails will be sent")
        support_email = self._prompt(
            "Support email address",
            f"support@{primary_domain}",
            validator=self._validate_email
        )
        
        # Mailgun domain
        self._print_info("Domain configured in Mailgun for sending emails")
        mailgun_domain = self._prompt(
            "Mailgun domain",
            primary_domain,
            validator=self._validate_domain
        )
        
        self.client_data['domains'] = {
            'primary': normalize_domain(primary_domain),
            'support': support_email,
            'mailgun': normalize_domain(mailgun_domain)
        }
        
        print(f"{Colors.OKGREEN}✓ Domain configuration collected{Colors.ENDC}")
        print()
    
    def _collect_contact_info(self):
        """Collect contact information."""
        print(f"{Colors.BOLD}Step 3: Contact Information{Colors.ENDC}")
        print("─" * 50)
        
        # Primary contact
        primary_contact = self._prompt(
            "Primary contact email",
            self.client_data['domains']['support'],
            validator=self._validate_email
        )
        
        # Escalation contact
        escalation_contact = self._prompt(
            "Escalation contact email",
            primary_contact,
            validator=self._validate_email
        )
        
        # Billing contact
        billing_contact = self._prompt(
            "Billing contact email",
            primary_contact,
            validator=self._validate_email
        )
        
        self.client_data['contacts'] = {
            'primary_contact': primary_contact,
            'escalation_contact': escalation_contact,
            'billing_contact': billing_contact
        }
        
        print(f"{Colors.OKGREEN}✓ Contact information collected{Colors.ENDC}")
        print()
    
    def _collect_routing_config(self):
        """Collect email routing configuration."""
        print(f"{Colors.BOLD}Step 4: Email Routing Setup{Colors.ENDC}")
        print("─" * 50)
        
        self._print_info("Configure where different types of emails should be routed")
        
        # Default categories
        categories = ['support', 'billing', 'sales', 'general']
        routing = {}
        
        for category in categories:
            default_email = self.client_data['contacts']['primary_contact']
            if category == 'billing':
                default_email = self.client_data['contacts']['billing_contact']
            
            routing[category] = self._prompt(
                f"{category.title()} emails route to",
                default_email,
                validator=self._validate_email
            )
        
        # Response times
        response_times = {}
        default_times = {
            'support': 'within 4 hours',
            'billing': 'within 24 hours', 
            'sales': 'within 2 hours',
            'general': 'within 24 hours'
        }
        
        print()
        self._print_info("Configure response time commitments")
        for category in categories:
            response_times[category] = self._prompt(
                f"{category.title()} response time",
                default_times[category]
            )
        
        self.client_data['routing'] = routing
        self.client_data['response_times'] = response_times
        
        print(f"{Colors.OKGREEN}✓ Routing configuration collected{Colors.ENDC}")
        print()
    
    def _collect_branding_config(self):
        """Collect branding configuration."""
        print(f"{Colors.BOLD}Step 5: Branding Configuration{Colors.ENDC}")
        print("─" * 50)
        
        # Company name for emails
        company_name = self._prompt(
            "Company name for emails",
            self.client_data['client']['name']
        )
        
        # Email signature
        email_signature = self._prompt(
            "Email signature",
            f"{company_name} Support Team"
        )
        
        # Brand colors
        self._print_info("Brand colors will be used in email templates (hex format)")
        primary_color = self._prompt(
            "Primary brand color",
            "#667eea",
            validator=self._validate_hex_color
        )
        
        secondary_color = self._prompt(
            "Secondary brand color", 
            "#764ba2",
            validator=self._validate_hex_color
        )
        
        self.client_data['branding'] = {
            'company_name': company_name,
            'email_signature': email_signature,
            'primary_color': primary_color if primary_color.startswith('#') else f"#{primary_color}",
            'secondary_color': secondary_color if secondary_color.startswith('#') else f"#{secondary_color}"
        }
        
        print(f"{Colors.OKGREEN}✓ Branding configuration collected{Colors.ENDC}")
        print()
    
    def _collect_settings_config(self):
        """Collect settings configuration."""
        print(f"{Colors.BOLD}Step 6: Feature Settings{Colors.ENDC}")
        print("─" * 50)
        
        # Feature flags
        settings = {}
        
        features = [
            ('auto_reply_enabled', 'Enable automatic customer replies', True),
            ('team_forwarding_enabled', 'Enable team member forwarding', True),
            ('ai_classification_enabled', 'Enable AI email classification', True),
            ('escalation_enabled', 'Enable automatic escalation', True),
            ('monitoring_enabled', 'Enable monitoring and analytics', True)
        ]
        
        for setting_key, description, default in features:
            choice = self._prompt_choice(
                description,
                ['Yes', 'No'],
                'Yes' if default else 'No'
            )
            settings[setting_key] = choice == 'Yes'
        
        self.client_data['settings'] = settings
        
        print(f"{Colors.OKGREEN}✓ Settings configuration collected{Colors.ENDC}")
        print()
    
    def _generate_config_files(self):
        """Generate configuration files."""
        print(f"{Colors.BOLD}Step 7: Generating Configuration Files{Colors.ENDC}")
        print("─" * 50)
        
        client_id = self.client_data['client']['id']
        client_dir = self.clients_dir / client_id
        client_dir.mkdir(exist_ok=True)
        
        # Copy AI context templates
        ai_context_dir = client_dir / "ai-context"
        ai_context_dir.mkdir(exist_ok=True)
        
        # Copy template files if they exist
        if self.templates_dir.exists():
            import shutil
            template_ai_dir = self.templates_dir / "ai-context"
            if template_ai_dir.exists():
                for template_file in template_ai_dir.glob("*"):
                    shutil.copy2(template_file, ai_context_dir)
        
        # Generate client-config.yaml
        client_config = {
            'client': self.client_data['client'],
            'domains': self.client_data['domains'],
            'branding': self.client_data['branding'],
            'response_times': self.client_data['response_times'],
            'contacts': self.client_data['contacts'],
            'settings': self.client_data['settings']
        }
        
        config_file = client_dir / "client-config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(client_config, f, default_flow_style=False, sort_keys=False)
        
        # Generate routing-rules.yaml
        routing_config = {
            'routing': self.client_data['routing'],
            'escalation': None,  # Can be configured later
            'backup_routing': None,  # Can be configured later
            'special_rules': None  # Can be configured later
        }
        
        routing_file = client_dir / "routing-rules.yaml"
        with open(routing_file, 'w') as f:
            yaml.dump(routing_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"{Colors.OKGREEN}✓ Configuration files generated{Colors.ENDC}")
        print()
    
    def _validate_configuration(self):
        """Validate the generated configuration."""
        print(f"{Colors.BOLD}Step 8: Validating Configuration{Colors.ENDC}")
        print("─" * 50)
        
        try:
            client_id = self.client_data['client']['id']
            
            # Try to load and validate the configuration
            from app.utils.client_loader import load_client_config
            config = load_client_config(client_id)
            
            # Basic validation
            assert config.client.id == client_id
            assert config.domains.primary
            assert config.contacts.primary_contact
            
            print(f"{Colors.OKGREEN}✓ Configuration validation passed{Colors.ENDC}")
            
        except Exception as e:
            self._print_warning(f"Configuration validation failed: {e}")
            self._print_info("The client has been created but may need manual review")
        
        print()


def main():
    """Main entry point for the onboarding wizard."""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Email Router Client Onboarding Wizard")
        print("Usage: python cli/client_onboarding.py")
        print()
        print("This interactive wizard will guide you through setting up")
        print("a new client configuration for the email router system.")
        return
    
    wizard = ClientOnboardingWizard()
    wizard.run()


if __name__ == '__main__':
    main() 