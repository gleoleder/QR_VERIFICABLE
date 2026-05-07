"""
test_api.py - Script de prueba rápida de la API

Verifica que todos los endpoints funcionen correctamente.

Uso:
    python test_api.py

Requisitos:
    - Servidor corriendo en http://localhost:5000
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"


def test_health():
    """Prueba el health check."""
    print("\n" + "=" * 50)
    print("TEST: Health Check")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/health")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    
    print("✓ Health check passed")
    return True


def test_issue_certificate():
    """Prueba la emisión de un certificado."""
    print("\n" + "=" * 50)
    print("TEST: Emisión de Certificado")
    print("=" * 50)
    
    payload = {
        "participant_name": "Test User",
        "course_name": "Curso de Prueba",
        "course_hours": 10,
        "institution": "Test Institution"
    }
    
    response = requests.post(
        f"{BASE_URL}/issue",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    assert response.status_code == 201
    assert data['success'] == True
    assert 'token' in data
    assert 'qr_code' in data
    assert 'verification_url' in data
    
    print("✓ Emisión de certificado passed")
    
    return data['token']


def test_verify_certificate(token):
    """Prueba la verificación de un certificado."""
    print("\n" + "=" * 50)
    print("TEST: Verificación de Certificado")
    print("=" * 50)
    
    # Prueba con Accept: application/pdf (descarga)
    response = requests.get(
        f"{BASE_URL}/verify/{token}",
        headers={"Accept": "application/pdf"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
    
    assert response.status_code == 200
    assert 'application/pdf' in response.headers.get('Content-Type', '')
    
    # Guardar PDF de prueba
    with open(f"test_certificate_{token[:8]}.pdf", 'wb') as f:
        f.write(response.content)
    
    print(f"✓ PDF guardado como: test_certificate_{token[:8]}.pdf")
    print("✓ Verificación de certificado passed")
    
    return True


def test_verify_invalid_token():
    """Prueba verificación con token inválido."""
    print("\n" + "=" * 50)
    print("TEST: Token Inválido")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/verify/00000000-0000-0000-0000-000000000000")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 404
    
    print("✓ Token inválido test passed")
    return True


def test_issue_invalid_data():
    """Prueba emisión con datos inválidos."""
    print("\n" + "=" * 50)
    print("TEST: Datos Inválidos")
    print("=" * 50)
    
    # Datos incompletos
    payload = {
        "participant_name": ""  # Vacío es inválido
    }
    
    response = requests.post(
        f"{BASE_URL}/issue",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 400
    assert response.json()['success'] == False
    
    print("✓ Datos inválidos test passed")
    return True


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "=" * 60)
    print("SISTEMA DE CERTIFICADOS QR - PRUEBAS DE API")
    print("=" * 60)
    
    try:
        # Verificar que el servidor esté corriendo
        try:
            requests.get(f"{BASE_URL}/health", timeout=5)
        except requests.exceptions.ConnectionError:
            print("\n✗ ERROR: No se pudo conectar al servidor")
            print(f"   Asegúrese de que el servidor esté corriendo en {BASE_URL}")
            print("   Ejecute: python app.py")
            sys.exit(1)
        
        # Ejecutar pruebas
        test_health()
        
        token = test_issue_certificate()
        
        test_verify_certificate(token)
        
        test_verify_invalid_token()
        
        test_issue_invalid_data()
        
        # Resumen
        print("\n" + "=" * 60)
        print("TODAS LAS PRUEBAS PASARON ✓")
        print("=" * 60)
        print(f"\nToken de prueba generado: {token}")
        print(f"URL de verificación: {BASE_URL}/verify/{token}")
        
    except AssertionError as e:
        print(f"\n✗ PRUEBA FALLÓ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR INESPERADO: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
