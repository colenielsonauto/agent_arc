#!/usr/bin/env python3
"""
CLI utility for managing email router clients and system status.
🔧 Provides commands for viewing, validating, and managing client configurations.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List
import json
from tabulate import tabulate

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.client_manager import EnhancedClientManager
from app.utils.client_loader import get_available_clients
from app.utils.domain_resolver import normalize_domain


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


class ClientManagerCLI:
    """CLI interface for managing email router clients."""
    
    def __init__(self):
        """Initialize the CLI manager."""
        self.manager = EnhancedClientManager()
    
    def list_clients(self, verbose: bool = False):
        """List all available clients."""
        try:
            clients = self.manager.get_available_clients()
            
            if not clients:
                print(f"{Colors.WARNING}No clients found.{Colors.ENDC}")
                return
            
            print(f"{Colors.HEADER}{Colors.BOLD}📧 Email Router Clients{Colors.ENDC}")
            print("=" * 60)
            
            if not verbose:
                # Simple list
                for client_id in clients:
                    print(f"  • {client_id}")
                print(f"\nTotal: {len(clients)} clients")
            else:
                # Detailed table
                table_data = []
                for client_id in clients:
                    try:
                        summary = self.manager.get_client_summary(client_id)
                        table_data.append([
                            client_id,
                            summary.get('name', 'N/A'),
                            summary.get('industry', 'N/A'),
                            summary.get('status', 'N/A'),
                            summary.get('total_domains', 0),
                            len(summary.get('routing_categories', []))
                        ])
                    except Exception as e:
                        table_data.append([client_id, f"Error: {e}", "", "", "", ""])
                
                headers = ["Client ID", "Name", "Industry", "Status", "Domains", "Routes"]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
        except Exception as e:
            print(f"{Colors.FAIL}Error listing clients: {e}{Colors.ENDC}")
    
    def show_client(self, client_id: str):
        """Show detailed information about a specific client."""
        try:
            summary = self.manager.get_client_summary(client_id)
            
            if 'error' in summary:
                print(f"{Colors.FAIL}Error loading client {client_id}: {summary['error']}{Colors.ENDC}")
                return
            
            print(f"{Colors.HEADER}{Colors.BOLD}📋 Client Details: {client_id}{Colors.ENDC}")
            print("=" * 60)
            
            # Basic info
            print(f"{Colors.BOLD}Basic Information:{Colors.ENDC}")
            print(f"  Name: {summary['name']}")
            print(f"  Industry: {summary['industry']}")
            print(f"  Status: {summary['status']}")
            print()
            
            # Domain info
            print(f"{Colors.BOLD}Domain Configuration:{Colors.ENDC}")
            print(f"  Primary Domain: {summary['primary_domain']}")
            print(f"  Total Domains: {summary['total_domains']}")
            if summary['domains']:
                print(f"  All Domains:")
                for domain in sorted(summary['domains'])[:10]:  # Show first 10
                    print(f"    • {domain}")
                if len(summary['domains']) > 10:
                    print(f"    ... and {len(summary['domains']) - 10} more")
            print()
            
            # Routing info
            print(f"{Colors.BOLD}Routing Configuration:{Colors.ENDC}")
            for category in summary['routing_categories']:
                destination = self.manager.get_routing_destination(client_id, category)
                response_time = self.manager.get_response_time(client_id, category)
                print(f"  {category}: {destination} ({response_time})")
            print()
            
            # Settings
            print(f"{Colors.BOLD}Settings:{Colors.ENDC}")
            for setting, value in summary['settings'].items():
                status = "✅" if value else "❌"
                print(f"  {setting}: {status}")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error showing client {client_id}: {e}{Colors.ENDC}")
    
    def validate_client(self, client_id: str):
        """Validate a client's configuration."""
        try:
            print(f"{Colors.OKBLUE}Validating client: {client_id}{Colors.ENDC}")
            
            is_valid = self.manager.validate_client_setup(client_id)
            
            if is_valid:
                print(f"{Colors.OKGREEN}✅ Client configuration is valid{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ Client configuration has issues{Colors.ENDC}")
                
        except Exception as e:
            print(f"{Colors.FAIL}Error validating client {client_id}: {e}{Colors.ENDC}")
    
    def validate_all_clients(self):
        """Validate all client configurations."""
        try:
            clients = self.manager.get_available_clients()
            
            print(f"{Colors.HEADER}{Colors.BOLD}🔍 Validating All Clients{Colors.ENDC}")
            print("=" * 60)
            
            results = []
            for client_id in clients:
                try:
                    is_valid = self.manager.validate_client_setup(client_id)
                    status = "✅ Valid" if is_valid else "❌ Invalid"
                    results.append([client_id, status])
                except Exception as e:
                    results.append([client_id, f"❌ Error: {e}"])
            
            print(tabulate(results, headers=["Client ID", "Status"], tablefmt="grid"))
            
            valid_count = sum(1 for _, status in results if status == "✅ Valid")
            print(f"\nSummary: {valid_count}/{len(clients)} clients valid")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error validating clients: {e}{Colors.ENDC}")
    
    def test_domain_resolution(self, domain: str):
        """Test domain resolution for client identification."""
        try:
            print(f"{Colors.OKBLUE}Testing domain resolution for: {domain}{Colors.ENDC}")
            print("-" * 50)
            
            # Normalize domain
            normalized = normalize_domain(domain)
            print(f"Normalized domain: {normalized}")
            
            # Test identification
            result = self.manager.identify_client_by_domain(domain)
            
            print(f"\nIdentification Result:")
            print(f"  Client ID: {result.client_id}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Method: {result.method}")
            print(f"  Domain Used: {result.domain_used}")
            print(f"  Successful: {'✅' if result.is_successful else '❌'}")
            
            # Show similar clients if no exact match
            if not result.is_successful:
                similar = self.manager.find_similar_clients(domain, limit=3)
                if similar:
                    print(f"\nSimilar clients:")
                    for client_id, similarity in similar:
                        print(f"  • {client_id} (similarity: {similarity:.2f})")
                else:
                    print(f"\nNo similar clients found.")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error testing domain resolution: {e}{Colors.ENDC}")
    
    def test_email_identification(self, email: str):
        """Test email-based client identification."""
        try:
            print(f"{Colors.OKBLUE}Testing email identification for: {email}{Colors.ENDC}")
            print("-" * 50)
            
            result = self.manager.identify_client_by_email(email)
            
            print(f"Identification Result:")
            print(f"  Client ID: {result.client_id}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Method: {result.method}")
            print(f"  Domain Used: {result.domain_used}")
            print(f"  Successful: {'✅' if result.is_successful else '❌'}")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error testing email identification: {e}{Colors.ENDC}")
    
    def show_system_status(self):
        """Show overall system status."""
        try:
            print(f"{Colors.HEADER}{Colors.BOLD}🔧 Email Router System Status{Colors.ENDC}")
            print("=" * 60)
            
            # Client count
            clients = self.manager.get_available_clients()
            print(f"Total Clients: {len(clients)}")
            
            # Domain mapping stats
            total_domains = 0
            valid_clients = 0
            
            for client_id in clients:
                try:
                    domains = self.manager.get_client_domains(client_id)
                    total_domains += len(domains)
                    
                    if self.manager.validate_client_setup(client_id):
                        valid_clients += 1
                except:
                    pass
            
            print(f"Total Domains Mapped: {total_domains}")
            print(f"Valid Clients: {valid_clients}/{len(clients)}")
            
            # Feature capabilities
            print(f"\nSystem Capabilities:")
            print(f"  ✅ Multi-tenant client identification")
            print(f"  ✅ Advanced domain resolution")
            print(f"  ✅ Fuzzy domain matching")
            print(f"  ✅ Hierarchy-based routing")
            print(f"  ✅ Confidence scoring")
            
            # Configuration health
            print(f"\nConfiguration Health:")
            health_score = (valid_clients / len(clients)) * 100 if clients else 0
            if health_score >= 90:
                health_status = f"{Colors.OKGREEN}Excellent"
            elif health_score >= 70:
                health_status = f"{Colors.WARNING}Good"
            else:
                health_status = f"{Colors.FAIL}Needs Attention"
            
            print(f"  Overall Health: {health_status} ({health_score:.1f}%){Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error getting system status: {e}{Colors.ENDC}")
    
    def refresh_client(self, client_id: str):
        """Refresh a client's configuration."""
        try:
            print(f"{Colors.OKBLUE}Refreshing client: {client_id}{Colors.ENDC}")
            self.manager.refresh_client(client_id)
            print(f"{Colors.OKGREEN}✅ Client refreshed successfully{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error refreshing client {client_id}: {e}{Colors.ENDC}")
    
    def refresh_all_clients(self):
        """Refresh all client configurations."""
        try:
            print(f"{Colors.OKBLUE}Refreshing all client configurations...{Colors.ENDC}")
            self.manager.refresh_all_clients()
            print(f"{Colors.OKGREEN}✅ All clients refreshed successfully{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error refreshing clients: {e}{Colors.ENDC}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Email Router Client Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                              # List all clients
  %(prog)s list --verbose                    # List clients with details
  %(prog)s show client-001-acme-corp         # Show client details
  %(prog)s validate client-001-acme-corp     # Validate specific client
  %(prog)s validate-all                      # Validate all clients
  %(prog)s test-domain company.com           # Test domain resolution
  %(prog)s test-email user@company.com       # Test email identification
  %(prog)s status                            # Show system status
  %(prog)s refresh client-001-acme-corp      # Refresh client config
  %(prog)s refresh-all                       # Refresh all clients
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all clients')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show client details')
    show_parser.add_argument('client_id', help='Client ID to show')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate client configuration')
    validate_parser.add_argument('client_id', help='Client ID to validate')
    
    # Validate all command
    subparsers.add_parser('validate-all', help='Validate all client configurations')
    
    # Test domain command
    test_domain_parser = subparsers.add_parser('test-domain', help='Test domain resolution')
    test_domain_parser.add_argument('domain', help='Domain to test')
    
    # Test email command
    test_email_parser = subparsers.add_parser('test-email', help='Test email identification')
    test_email_parser.add_argument('email', help='Email address to test')
    
    # Status command
    subparsers.add_parser('status', help='Show system status')
    
    # Refresh command
    refresh_parser = subparsers.add_parser('refresh', help='Refresh client configuration')
    refresh_parser.add_argument('client_id', help='Client ID to refresh')
    
    # Refresh all command
    subparsers.add_parser('refresh-all', help='Refresh all client configurations')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = ClientManagerCLI()
    
    try:
        if args.command == 'list':
            cli.list_clients(verbose=args.verbose)
        elif args.command == 'show':
            cli.show_client(args.client_id)
        elif args.command == 'validate':
            cli.validate_client(args.client_id)
        elif args.command == 'validate-all':
            cli.validate_all_clients()
        elif args.command == 'test-domain':
            cli.test_domain_resolution(args.domain)
        elif args.command == 'test-email':
            cli.test_email_identification(args.email)
        elif args.command == 'status':
            cli.show_system_status()
        elif args.command == 'refresh':
            cli.refresh_client(args.client_id)
        elif args.command == 'refresh-all':
            cli.refresh_all_clients()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Operation cancelled by user.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == '__main__':
    main() 