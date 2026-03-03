import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_KEY", "")

try:
    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"Failed to initialize Supabase client: {e}")
    supabase = None

def get_setting(key_name: str) -> str:
    if not supabase: return None
    try:
        response = supabase.table('settings').select('value').eq('key', key_name).execute()
        if response.data:
            return response.data[0]['value']
    except Exception as e:
        print(f"Error getting setting {key_name}: {e}")
    return None

def update_setting(key_name: str, value: str):
    if not supabase: return
    try:
        supabase.table('settings').upsert({'key': key_name, 'value': value}).execute()
    except Exception as e:
        print(f"Error updating setting {key_name}: {e}")

def get_all_settings():
    if not supabase: return {}
    try:
        response = supabase.table('settings').select('*').execute()
        return {row['key']: row['value'] for row in response.data}
    except Exception as e:
        print(f"Error getting all settings: {e}")
        return {}

def add_user(user_id: int, username: str, first_name: str, last_name: str):
    if not supabase: return
    try:
        supabase.table('users').upsert({
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name
        }).execute()
    except Exception as e:
        print(f"Error adding user {user_id}: {e}")

def get_user(user_id: int):
    if not supabase: return None
    try:
        response = supabase.table('users').select('*').eq('user_id', user_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Error getting user {user_id}: {e}")
    return None

def update_user_status(user_id: int, status: str):
    if not supabase: return
    try:
        supabase.table('users').update({'status': status}).eq('user_id', user_id).execute()
    except Exception as e:
        print(f"Error updating user {user_id} status: {e}")

def get_users_by_status(status: str = None):
    if not supabase: return []
    try:
        if status is None:
            return supabase.table('users').select('*').execute().data
        return supabase.table('users').select('*').eq('status', status).execute().data
    except Exception as e:
        print(f"Error getting users by status {status}: {e}")
        return []

def add_payment(user_id: int, amount: float, screenshot_file_id: str) -> str:
    if not supabase: return None
    try:
        response = supabase.table('payments').insert({
            'user_id': user_id,
            'amount': amount,
            'screenshot_file_id': screenshot_file_id
        }).execute()
        if response.data:
            return response.data[0]['id']
    except Exception as e:
        print(f"Error adding payment for {user_id}: {e}")
    return None

def update_payment_status(payment_id: str, status: str):
    if not supabase: return
    try:
        supabase.table('payments').update({'status': status}).eq('id', payment_id).execute()
    except Exception as e:
        print(f"Error updating payment {payment_id} status: {e}")

def get_payment(payment_id: str):
    if not supabase: return None
    try:
        response = supabase.table('payments').select('*').eq('id', payment_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Error getting payment {payment_id}: {e}")
    return None

def get_stats():
    if not supabase: return {'total_users': 0, 'total_payments': 0, 'pending': 0, 'confirmed': 0, 'rejected': 0}
    try:
        users_resp = supabase.table('users').select('user_id', count='exact').execute()
        payments_resp = supabase.table('payments').select('*').execute()
        
        total_users = users_resp.count if users_resp.count is not None else 0
        total_payments = len(payments_resp.data) if payments_resp.data else 0
        pending_payments = sum(1 for p in payments_resp.data if p.get('status') == 'pending') if payments_resp.data else 0
        confirmed_payments = sum(1 for p in payments_resp.data if p.get('status') == 'confirmed') if payments_resp.data else 0
        rejected_payments = sum(1 for p in payments_resp.data if p.get('status') == 'rejected') if payments_resp.data else 0
        
        return {
            'total_users': total_users,
            'total_payments': total_payments,
            'pending': pending_payments,
            'confirmed': confirmed_payments,
            'rejected': rejected_payments
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {'total_users': 0, 'total_payments': 0, 'pending': 0, 'confirmed': 0, 'rejected': 0}
