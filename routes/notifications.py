from flask import Blueprint, jsonify, session
from services.notification_service import NotificationService

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('', methods=['GET'])
def get_notifications():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    notifs = NotificationService.get_user_notifications(user_id)
    unread_count = sum(1 for n in notifs if n['read_status'] == 0)
    return jsonify({
        'success': True,
        'notifications': notifs,
        'unread_count': unread_count
    })

@notifications_bp.route('/<int:notif_id>/read', methods=['PUT'])
def mark_read(notif_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    NotificationService.mark_as_read(notif_id, user_id)
    return jsonify({'success': True})

@notifications_bp.route('/read-all', methods=['PUT'])
def mark_all_read():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    NotificationService.mark_all_as_read(user_id)
    return jsonify({'success': True})
