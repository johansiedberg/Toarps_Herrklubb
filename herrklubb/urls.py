from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    CustomLoginView, update_account_settings_view, upload_avatar_view,
    hub_view, herrklubb_view, vote_bucket_item, toggle_bucket_dream,
    add_bucket_item, edit_bucket_item, delete_bucket_item, complete_bucket_item, save_user_bucket_votes,
    calendar_view, add_unavailability_view, delete_unavailability_view,
    save_herrklubb_event_view, delete_herrklubb_event_view, toggle_event_coordinator_view,
    toggle_event_participation_view,
    predictions_sso_login
)

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('account/settings/', update_account_settings_view, name='update_account_settings'),
    path('hub/', hub_view, name='hub'),
    path('herrklubb/', herrklubb_view, name='herrklubb'),
    path('herrklubb/save/', save_user_bucket_votes, name='herrklubb_save_votes'),
    path('herrklubb/vote/', vote_bucket_item, name='herrklubb_vote'),
    path('herrklubb/dream/', toggle_bucket_dream, name='herrklubb_dream'),
    path('herrklubb/add/', add_bucket_item, name='herrklubb_add_item'),
    path('herrklubb/edit/<int:item_id>/', edit_bucket_item, name='herrklubb_edit_item'),
    path('herrklubb/delete/<int:item_id>/', delete_bucket_item, name='herrklubb_delete_item'),
    path('herrklubb/complete/<int:item_id>/', complete_bucket_item, name='herrklubb_complete_item'),
    path('herrklubb/kalender/', calendar_view, name='calendar'),
    path('herrklubb/kalender/add/', add_unavailability_view, name='add_unavailability'),
    path('herrklubb/kalender/delete/<int:item_id>/', delete_unavailability_view, name='delete_unavailability'),
    path('herrklubb/event/save/', save_herrklubb_event_view, name='save_herrklubb_event'),
    path('herrklubb/event/delete/<int:event_id>/', delete_herrklubb_event_view, name='delete_herrklubb_event'),
    path('herrklubb/event/coordinator/<int:event_id>/', toggle_event_coordinator_view, name='toggle_event_coordinator'),
    path('herrklubb/event/participant/<int:event_id>/<str:status>/', toggle_event_participation_view, name='toggle_event_participation'),
    path('predictions/login/', predictions_sso_login, name='predictions_sso_login'),
    path('profile/avatar/', upload_avatar_view, name='upload_avatar'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
