#!/bin/bash

# SSL Certificate Generation Script for Asmblr
# Generates self-signed certificates for HTTPS

set -e

CERTS_DIR="certs"
CERT_KEY="$CERTS_DIR/key.pem"
CERT_CSR="$CERTS_DIR/cert.csr"
CERT_CRT="$CERTS_DIR/cert.pem"
CERT_CA="$CERTS_DIR/ca.pem"
CA_KEY="$CERTS_DIR/ca-key.pem"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔒 Generating SSL Certificates for Asmblr${NC}"
echo "=================================="

# Create certs directory
mkdir -p "$CERTS_DIR"
echo -e "${YELLOW}📁 Created certs directory${NC}"

# Generate CA private key
echo -e "${YELLOW}🔑 Generating CA private key...${NC}"
openssl genrsa -out "$CA_KEY" 4096
echo -e "${GREEN}✅ CA private key generated${NC}"

# Generate CA certificate
echo -e "${YELLOW}📜 Generating CA certificate...${NC}"
openssl req -new -x509 -days 365 -nodes -out "$CERT_CA" -key "$CA_KEY" -subj "/C=US/ST=State/L=City/O=Asmblr/CN=Asmblr-CA" > /dev/null 2>&1
echo -e "${GREEN}✅ CA certificate generated${NC}"

# Generate server private key
echo -e "${YELLOW}🔑 Generating server private key...${NC}"
openssl genrsa -out "$CERT_KEY" 2048
echo -e "${GREEN}✅ Server private key generated${NC}"

# Generate CSR
echo -e "${YELLOW}📝 Generating certificate signing request...${NC}"
openssl req -new -key "$CERT_KEY" -out "$CERT_CSR" -subj "/C=US/ST=State/L=City/O=Asmblr/CN=localhost" > /dev/null 2>&1
echo -e "${GREEN}✅ CSR generated${NC}"

# Generate server certificate
echo -e "${YELLOW}📜 Generating server certificate...${NC}"
openssl x509 -req -in "$CERT_CSR" -CA "$CERT_CA" -CAkey "$CA_KEY" -CAcreateserial -out "$CERT_CRT" -days 365 -extensions v3_req \
  -extfile <(printf "
[v3_req]
basicConstraints = critical, CA:FALSE
subjectAltName = @alt_names
[alt_names]
DNS.1 = localhost
DNS.2 = api.localhost
DNS.3 = ui.localhost
DNS.4 = asmblr.local
IP.1 = 127.0.0.1
IP.2 = ::1
") > /dev/null 2>&1
echo -e "${GREEN}✅ Server certificate generated${NC}"

# Clean up CSR
rm -f "$CERT_CSR"

# Set appropriate permissions
echo -e "${YELLOW}🔒 Setting permissions...${NC}"
chmod 600 "$CERT_KEY" "$CA_KEY"
chmod 644 "$CERT_CRT" "$CERT_CA"
echo -e "${GREEN}✅ Permissions set${NC}"

# Display certificate info
echo -e "${GREEN}📋 Certificate Information:${NC}"
openssl x509 -in "$CERT_CRT" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:|DNS:|IP:)" | head -10

echo -e "${GREEN}🎉 SSL certificates generated successfully!${NC}"
echo -e "${YELLOW}📍 Files created:${NC}"
echo "  - $CERT_CA (CA Certificate)"
echo "  - $CERT_CRT (Server Certificate)"
echo "  - $CERT_KEY (Server Private Key)"
echo ""
echo -e "${GREEN}🚀 To use with docker-compose.secure.yml:${NC}"
echo "  docker-compose -f docker-compose.secure.yml up"
echo ""
echo -e "${YELLOW}⚠️  For production, replace with CA-signed certificates${NC}"
