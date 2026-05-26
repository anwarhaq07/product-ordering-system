#Order states
ORDER_STATES = ["PENDING", "CONFIRMED", "DELIVERED", "CANCELLED"]

#Allowed transitions
ALLOWED_TRANSITIONS = {
    "PENDING" : ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["DELIVERED", "CANCELLED"],
    "DELIVERED": [],
    "CANCELLED":[]
    }

def can_transition(current_status, new_status):
    return new_status in ALLOWED_TRANSITIONS.get(current_status, [])