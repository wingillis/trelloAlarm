def filter_for_device(notifs, device):
    return [x for x in notifs if x.get('target_device_iden') == device.device_iden]

def filter_for_text(notifs, text):
    return [x for x in notifs if text.lower() in x.get('body').lower()]
