from django.urls import path
from . import dashboard_views
from . import views  

app_name = 'dashboard'   

urlpatterns = [
    path('', dashboard_views.dashboard_view, name='main'),
    path('users/', dashboard_views.dashboard_users, name='users'),
    path('manage-users/departments/', dashboard_views.dashboard_departments, name='departments'),
    path('groups/', dashboard_views.dashboard_groups, name='groups'),
    path('locations/', dashboard_views.locations_list, name='locations'),
    
    # path('request-types/', dashboard_views.dashboard_request_types, name='request_types'),
    # path('checklists/', dashboard_views.dashboard_checklists, name='checklists'),
    # path('complaints/', dashboard_views.complaints, name='complaints'),
    # path('breakfast-vouchers/', dashboard_views.breakfast_vouchers, name='breakfast_vouchers'),
    # path('reviews/', dashboard_views.reviews, name='reviews'),
    # CRUD endpoints
    path('users/create/', dashboard_views.user_create, name='user_create'),
    path('users/<int:user_id>/update/', dashboard_views.user_update, name='user_update'),
    path('users/<int:user_id>/delete/', dashboard_views.user_delete, name='user_delete'),
    path('manage-users/departments/create/', dashboard_views.department_create, name='department_create'),
    path('manage-users/departments/<int:dept_id>/update/', dashboard_views.department_update, name='department_update'),
    path('manage-users/departments/<int:dept_id>/delete/', dashboard_views.department_delete, name='department_delete'),
    path('groups/create/', dashboard_views.group_create, name='group_create'),
    path('groups/<int:group_id>/update/', dashboard_views.group_update, name='group_update'),
    path('groups/<int:group_id>/delete/', dashboard_views.group_delete, name='group_delete'),
    # path('locations/create/', dashboard_views.location_create, name='location_create'),
    # path('locations/<int:loc_id>/update/', dashboard_views.location_update, name='location_update'),
    path('locations/<int:loc_id>/delete/', dashboard_views.location_delete, name='location_delete'),
    # path('request-types/create/', dashboard_views.request_type_create, name='request_type_create'),
    # path('request-types/<int:rt_id>/update/', dashboard_views.request_type_update, name='request_type_update'),
    # path('request-types/<int:rt_id>/delete/', dashboard_views.request_type_delete, name='request_type_delete'),
    path('checklists/create/', dashboard_views.checklist_create, name='checklist_create'),
    path('checklists/<int:cl_id>/update/', dashboard_views.checklist_update, name='checklist_update'),
    path('checklists/<int:cl_id>/delete/', dashboard_views.checklist_delete, name='checklist_delete'),
    path('complaints/create/', dashboard_views.complaint_create, name='complaint_create'),
    path('complaints/<int:complaint_id>/update/', dashboard_views.complaint_update, name='complaint_update'),
    path('complaints/<int:complaint_id>/delete/', dashboard_views.complaint_delete, name='complaint_delete'),
    path('vouchers/create/', dashboard_views.voucher_create, name='voucher_create'),
    path('vouchers/<int:voucher_id>/update/', dashboard_views.voucher_update, name='voucher_update'),
    path('vouchers/<int:voucher_id>/delete/', dashboard_views.voucher_delete, name='voucher_delete'),
    path('reviews/create/', dashboard_views.review_create, name='review_create'),
    path('reviews/<int:review_id>/update/', dashboard_views.review_update, name='review_update'),
    path('reviews/<int:review_id>/delete/', dashboard_views.review_delete, name='review_delete'),
    
    # New Voucher System URLs
    path('voucher-analytics/', dashboard_views.voucher_analytics, name='voucher_analytics'),
    path('guests/', dashboard_views.dashboard_guests, name='guests'),
    path('guests/<int:guest_id>/', dashboard_views.guest_detail, name='guest_detail'),
    path('vouchers/', dashboard_views.dashboard_vouchers, name='vouchers'),
    path('vouchers/<int:voucher_id>/', dashboard_views.voucher_detail, name='voucher_detail'),
    
    # Guest QR Codes Management
    path('guest-qr-codes/', dashboard_views.guest_qr_codes, name='guest_qr_codes'),
    path('guest-qr-codes/<int:guest_id>/regenerate/', dashboard_views.regenerate_guest_qr, name='regenerate_guest_qr'),
    path('guest-qr-codes/<int:guest_id>/share-whatsapp/', dashboard_views.share_guest_qr_whatsapp, name='share_guest_qr_whatsapp'),
    path('guest-qr-codes/<int:guest_id>/whatsapp-message/', dashboard_views.get_guest_whatsapp_message, name='get_guest_whatsapp_message'),
    
    # Voucher QR Code Management
    path('vouchers/<int:voucher_id>/regenerate-qr/', dashboard_views.regenerate_voucher_qr, name='regenerate_voucher_qr'),
    path('vouchers/<int:voucher_id>/share-whatsapp/', dashboard_views.share_voucher_whatsapp, name='share_voucher_whatsapp'),
    path('manage-users/', dashboard_views.manage_users, name='manage_users'),
    # Manage Users screens (new per-screen routes)
    path('manage-users/all/', dashboard_views.manage_users_all, name='manage_users_all'),
    path('manage-users/users/<int:user_id>/', dashboard_views.manage_user_detail, name='manage_user_detail'),
    # API endpoint for Manage Users polling
    path('api/manage-users/users/', dashboard_views.manage_users_api_users, name='api_manage_users_users'),
    path('api/manage-users/users/<int:user_id>/', dashboard_views.manage_users_api_users, name='api_manage_users_users_detail'),
    path('api/manage-users/users/<int:user_id>/reset-password/', dashboard_views.api_reset_user_password, name='api_reset_user_password'),
    path('api/manage-users/users/<int:user_id>/toggle-enabled/', dashboard_views.manage_users_toggle_enabled, name='api_manage_users_toggle_enabled'),
    path('api/manage-users/users/bulk-action/', dashboard_views.manage_users_api_bulk_action, name='api_manage_users_bulk_action'),
    # Filters endpoint used by the Manage Users frontend to populate selects
    path('api/manage-users/filters/', dashboard_views.api_manage_users_filters, name='api_manage_users_filters'),
    path('manage-users/groups/', dashboard_views.manage_users_groups, name='manage_users_groups'),
    # Group membership management
    path('manage-users/groups/<int:group_id>/add-member/', dashboard_views.add_group_member, name='add_group_member'),
    path('manage-users/groups/<int:group_id>/remove-member/', dashboard_views.remove_group_member, name='remove_group_member'),
    # API endpoints for groups dashboard
    path('api/groups/notify-all/', dashboard_views.api_notify_all_groups, name='api_groups_notify_all'),
    path('api/departments/<int:dept_id>/notify/', dashboard_views.api_notify_department, name='api_department_notify'),
    path('api/departments/<int:dept_id>/members/', dashboard_views.api_department_members, name='api_department_members'),
    path('manage-users/departments/<int:dept_id>/assign-lead/', dashboard_views.assign_department_lead, name='assign_department_lead'),
    path('api/departments/create/', dashboard_views.department_create, name='department_create'),
    path('api/groups/<int:group_id>/members/', dashboard_views.api_group_members, name='api_group_members'),
    path('api/groups/<int:group_id>/permissions/', dashboard_views.api_group_permissions, name='api_group_permissions'),
    path('api/groups/<int:group_id>/permissions/update/', dashboard_views.api_group_permissions_update, name='api_group_permissions_update'),
    path('api/groups/bulk-permissions/update/', dashboard_views.api_bulk_permissions_update, name='api_bulk_permissions_update'),
    path('manage-users/profiles/', dashboard_views.manage_users_profiles, name='manage_users_profiles'),
    path('tickets/', dashboard_views.tickets, name='tickets'),
    path('my-tickets/', dashboard_views.my_tickets, name='my_tickets'),
    path('tickets/<int:ticket_id>/', dashboard_views.ticket_detail, name='ticket_detail'),
    path('api/tickets/create/', dashboard_views.create_ticket_api, name='api_create_ticket'),
    path('api/tickets/<int:ticket_id>/assign/', dashboard_views.assign_ticket_api, name='api_assign_ticket'),
    # Removed claim_ticket_api as we're removing the claim functionality
    path('api/tickets/<int:ticket_id>/accept/', dashboard_views.accept_ticket_api, name='api_accept_ticket'),
    path('api/tickets/<int:ticket_id>/start/', dashboard_views.start_ticket_api, name='api_start_ticket'),
    path('api/tickets/<int:ticket_id>/complete/', dashboard_views.complete_ticket_api, name='api_complete_ticket'),
    path('api/tickets/<int:ticket_id>/close/', dashboard_views.close_ticket_api, name='api_close_ticket'),
    path('api/tickets/<int:ticket_id>/escalate/', dashboard_views.escalate_ticket_api, name='api_escalate_ticket'),
    path('api/tickets/<int:ticket_id>/reject/', dashboard_views.reject_ticket_api, name='api_reject_ticket'),
    path('configure-requests/', dashboard_views.configure_requests, name='configure_requests'),
    path('messaging-setup/', dashboard_views.messaging_setup, name='messaging_setup'),
    path('feedback/', dashboard_views.feedback_inbox, name='feedback_inbox'),
    path('feedback/<int:feedback_id>/', dashboard_views.feedback_detail, name='feedback_detail'),
    path('integrations/', dashboard_views.integrations, name='integrations'),
    path('sla-configuration/', dashboard_views.sla_configuration, name='sla_configuration'),
    path('api/sla-configuration/update/', dashboard_views.api_sla_configuration_update, name='api_sla_configuration_update'),
    path('analytics/', dashboard_views.analytics_dashboard, name='analytics'),
    path('performance/', dashboard_views.performance_dashboard, name='performance'),
    path('gym/', dashboard_views.gym, name='gym'),
    path('gym/report/', dashboard_views.gym_report, name='gym_report'),
    
    # Export/Import URLs
    path('export/users/', dashboard_views.export_user_data, name='export_user_data'),
    path('import/users/', dashboard_views.import_user_data, name='import_user_data'),
    path('clear/users/', dashboard_views.clear_user_data, name='clear_user_data'),
    
    # Ticket suggestions API
    path('api/tickets/suggestions/', dashboard_views.get_ticket_suggestions_api, name='api_ticket_suggestions'),
]