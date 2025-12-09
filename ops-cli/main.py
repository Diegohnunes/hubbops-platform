import sys
import json
import os

# Add ops-cli to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commands.create_service import create_service_command
from commands.rm_service import rm_service_command


def create_with_handler(template_id: str, config_json: str):
    """Create service using the new handler system"""
    from handlers import get_handler, ServiceConfig, list_supported_templates
    
    try:
        config = json.loads(config_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON config: {e}")
        sys.exit(1)
    
    name = config.get("service_name", "").lower().replace("_", "-").replace(" ", "-")
    if not name:
        print("❌ service_name is required in config")
        sys.exit(1)
    
    # Check if handler exists
    supported = list_supported_templates()
    if template_id not in supported:
        print(f"⚠️  No handler for template '{template_id}'")
        print(f"   Supported: {', '.join(supported)}")
        print(f"   Falling back to legacy create-service...")
        # Fall back to legacy for unsupported templates
        create_service_command(name, config.get("coin", "btc"), template_id)
        return
    
    service_config = ServiceConfig(
        name=name,
        template_id=template_id,
        config=config,
        base_dir=os.getcwd()
    )
    
    handler = get_handler(template_id, service_config)
    success = handler.execute()
    
    if not success:
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("HubbOps CLI - Service Management")
        print("\nUsage:")
        print("  # New handler-based creation (recommended)")
        print('  python ops-cli/main.py create --template <template-id> --config \'{"service_name": "my-api", ...}\'')
        print("")
        print("  # Legacy crypto collector creation")
        print("  python ops-cli/main.py create-service <name> <coin> <type>")
        print("  python ops-cli/main.py rm-service <name> <coin> <type>")
        print("\nTemplates:")
        try:
            from handlers import list_supported_templates
            for t in list_supported_templates():
                print(f"  - {t}")
        except ImportError:
            print("  (handlers not available)")
        sys.exit(1)

    command = sys.argv[1]

    # New handler-based create
    if command == "create":
        template_id = None
        config_json = None
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--template" and i + 1 < len(sys.argv):
                template_id = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--config" and i + 1 < len(sys.argv):
                config_json = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        if not template_id or not config_json:
            print("Usage: python ops-cli/main.py create --template <id> --config '<json>'")
            sys.exit(1)
        
        create_with_handler(template_id, config_json)

    # Legacy create-service (for crypto collectors)
    elif command == "create-service":
        if len(sys.argv) != 5:
            print("Usage: python ops-cli/main.py create-service <name> <coin> <type>")
            print("Example: python ops-cli/main.py create-service eth-collector eth collector")
            sys.exit(1)
        
        name = sys.argv[2]
        coin = sys.argv[3]
        service_type = sys.argv[4]
        
        create_service_command(name, coin, service_type)
    
    elif command == "rm-service":
        if len(sys.argv) != 5:
            print("Usage: python ops-cli/main.py rm-service <name> <coin> <type>")
            print("Example: python ops-cli/main.py rm-service eth-collector eth collector")
            sys.exit(1)
        
        name = sys.argv[2]
        coin = sys.argv[3]
        service_type = sys.argv[4]
        
        rm_service_command(name, coin, service_type)
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, create-service, rm-service")
        sys.exit(1)

if __name__ == "__main__":
    main()

