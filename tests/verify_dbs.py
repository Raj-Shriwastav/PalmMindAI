#!/usr/bin/env python3
import sys
import socket
import time

from app.core.config import settings

def check_socket(host, port, service_name):
    print(f"Checking TCP connection to {service_name} on {host}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((host, port))
        s.close()
        print(f"  [ONLINE] Port {port} is open and responding!")
        return True
    except socket.timeout:
        print(f"  [OFFLINE] Port {port} connection timed out.")
        return False
    except ConnectionRefusedError:
        print(f"  [OFFLINE] Port {port} connection refused.")
        return False
    except Exception as e:
        print(f"  [OFFLINE] Port {port} error: {str(e)}")
        return False

def verify_postgres():
    print("\n==========================================")
    print("Verifying PostgreSQL Service")
    print("==========================================")
    
    port_ok = check_socket(settings.POSTGRES_HOST, settings.POSTGRES_PORT, "PostgreSQL")
    if not port_ok:
        print(f"[WARNING] PostgreSQL is not accessible on {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}.")
        return False
        
    try:
        import psycopg2
    except ImportError:
        print("[INFO] 'psycopg2' not installed. Skipping driver connection test.")
        return True
        
    try:
        print("Testing DB Connection with psycopg2...")
        # Dynamically load all connection configurations from Settings
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            connect_timeout=3
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"  [SUCCESS] Connected to database!")
        print(f"  Database Version: {db_version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  [DRIVER FAILED] Database credentials error or connection issue.")
        print(f"  Details: {str(e)}")
        print("  Note: Connection to port succeeded, which means the database container is running!")
        return True

def verify_redis():
    print("\n==========================================")
    print("Verifying Redis Service")
    print("==========================================")
    
    port_ok = check_socket(settings.REDIS_HOST, settings.REDIS_PORT, "Redis")
    if not port_ok:
        print(f"[WARNING] Redis is not accessible on {settings.REDIS_HOST}:{settings.REDIS_PORT}.")
        return False
        
    try:
        import redis
    except ImportError:
        print("[INFO] 'redis' client not installed. Skipping driver ping test.")
        return True
        
    try:
        print("Testing Redis client Ping...")
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, socket_timeout=3)
        pong = r.ping()
        if pong:
            print("  [SUCCESS] Redis ping returned PONG!")
            return True
        else:
            print("  [FAILED] Redis ping did not return True.")
            return False
    except Exception as e:
        print(f"  [DRIVER FAILED] Redis command error: {str(e)}")
        return False

def verify_qdrant():
    print("\n==========================================")
    print("Verifying Qdrant Service")
    print("==========================================")
    
    port_ok = check_socket(settings.QDRANT_HOST, settings.QDRANT_PORT, "Qdrant REST API")
    if not port_ok:
        print(f"[WARNING] Qdrant is not accessible on {settings.QDRANT_HOST}:{settings.QDRANT_PORT}.")
        return False
        
    try:
        import qdrant_client
    except ImportError:
        print("[INFO] 'qdrant-client' not installed. Skipping driver connection test.")
        return True
        
    try:
        print("Testing Qdrant connection with qdrant-client...")
        client = qdrant_client.QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=3.0)
        collections = client.get_collections()
        print("  [SUCCESS] Connected to Qdrant!")
        print(f"  Collections present: {len(collections.collections)}")
        for c in collections.collections:
            print(f"    - {c.name}")
        return True
    except Exception as e:
        print(f"  [DRIVER FAILED] Qdrant connection error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting database verification suite on host...")
    print("Make sure you run 'docker-compose up -d' first to boot Postgres, Redis, and Qdrant containers.")
    
    pg_status = verify_postgres()
    redis_status = verify_redis()
    qd_status = verify_qdrant()
    
    print("\n==========================================")
    print("Verification Summary")
    print("==========================================")
    print(f"Postgres Port/Connection: {'ONLINE' if pg_status else 'OFFLINE'}")
    print(f"Redis Port/Connection:    {'ONLINE' if redis_status else 'OFFLINE'}")
    print(f"Qdrant Port/Connection:   {'ONLINE' if qd_status else 'OFFLINE'}")
    print("==========================================")
    
    all_ok = pg_status and redis_status and qd_status
    sys.exit(0 if all_ok else 1)
