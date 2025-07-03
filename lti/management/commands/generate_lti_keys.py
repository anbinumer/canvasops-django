from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import os


class Command(BaseCommand):
    help = 'Generate RSA key pair for LTI 1.3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing keys',
        )

    def handle(self, *args, **options):
        # Define key paths
        private_key_path = 'private.key'
        public_key_path = 'public.key'
        
        # Check if keys exist
        if os.path.exists(private_key_path) and not options['force']:
            self.stdout.write(
                self.style.WARNING('Keys already exist. Use --force to overwrite.')
            )
            return
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Write private key
        with open(private_key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Get public key
        public_key = private_key.public_key()
        
        # Write public key
        with open(public_key_path, 'wb') as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated RSA key pair:')
        )
        self.stdout.write(f'  Private key: {private_key_path}')
        self.stdout.write(f'  Public key: {public_key_path}')
        
        # Also create a JWK representation for Canvas
        import base64
        import json
        
        # Extract modulus and exponent
        public_numbers = public_key.public_numbers()
        
        # Convert to base64url encoding
        def to_base64url(data):
            return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')
        
        # Create JWK
        jwk = {
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": "canvasops-key-1",
            "n": to_base64url(public_numbers.n.to_bytes(
                (public_numbers.n.bit_length() + 7) // 8, 'big'
            )),
            "e": to_base64url(public_numbers.e.to_bytes(
                (public_numbers.e.bit_length() + 7) // 8, 'big'
            ))
        }
        
        # Write JWK
        with open('public.jwk', 'w') as f:
            json.dump({"keys": [jwk]}, f, indent=2)
        
        self.stdout.write(f'  JWK file: public.jwk')
        self.stdout.write(
            self.style.SUCCESS('\nKeys generated successfully!')
        )