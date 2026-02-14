from sqladmin import ModelView
from sqladmin.filters import (
    AllUniqueStringValuesFilter,
    BooleanFilter,
    ForeignKeyFilter,
    OperationColumnFilter,
)

from app.models import (
    FriendRequest,
    SyncEvent,
    SyncOp,
    SubTask,
    Tag,
    Task,
    User,
)


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    category = "Users"
    icon = "fa-solid fa-user"
    page_size = 25
    column_list = [
        User.id,
        User.email,
        User.name,
        User.provider,
        User.friend_tag,
        User.created_at,
    ]
    column_searchable_list = [User.email, User.name, User.friend_tag]
    column_sortable_list = [User.email, User.name, User.created_at]
    column_filters = [AllUniqueStringValuesFilter(User.provider)]
    column_labels = {
        User.friend_tag: "Friend tag",
        User.provider: "Provider",
    }
    form_excluded_columns = [User.password_hash]
    column_details_exclude_list = [User.password_hash]
    column_export_list = [
        User.id,
        User.email,
        User.name,
        User.provider,
        User.friend_tag,
        User.created_at,
    ]
    export_types = ["csv", "json"]


class TaskAdmin(ModelView, model=Task):
    name = "Task"
    name_plural = "Tasks"
    category = "Tasks"
    icon = "fa-solid fa-list-check"
    page_size = 25
    form_columns = [
        Task.title,
        Task.description,
        Task.user,
        Task.is_completed,
        Task.tags,
        Task.created_at,
        Task.updated_at,
    ]
    column_list = [
        Task.id,
        Task.title,
        Task.user,
        Task.is_completed,
        Task.created_at,
        Task.updated_at,
    ]
    column_formatters = {
        Task.user: lambda m, a: (m.user.email or m.user.name or str(m.user.id)) if m.user else "",
    }
    column_searchable_list = [Task.title]
    column_sortable_list = [Task.title, Task.is_completed, Task.created_at, Task.updated_at]
    column_filters = [
        BooleanFilter(Task.is_completed),
        ForeignKeyFilter(Task.user_id, User.email, User),
    ]
    column_labels = {
        Task.user: "User",
        Task.is_completed: "Completed",
        Task.tags: "Tags",
    }
    column_export_list = [
        Task.id,
        Task.title,
        Task.user_id,
        Task.is_completed,
        Task.created_at,
    ]
    export_types = ["csv", "json"]


class SubTaskAdmin(ModelView, model=SubTask):
    name = "SubTask"
    name_plural = "SubTasks"
    category = "Tasks"
    icon = "fa-solid fa-square-check"
    page_size = 25
    form_columns = [
        SubTask.text,
        SubTask.task,
        SubTask.is_completed,
        SubTask.created_at,
        SubTask.updated_at,
    ]
    column_list = [
        SubTask.id,
        SubTask.text,
        SubTask.task,
        SubTask.is_completed,
        SubTask.created_at,
    ]
    column_formatters = {
        SubTask.task: lambda m, a: m.task.title if m.task else "",
    }
    column_searchable_list = [SubTask.text]
    column_sortable_list = [SubTask.is_completed, SubTask.created_at]
    column_filters = [
        BooleanFilter(SubTask.is_completed),
        ForeignKeyFilter(SubTask.task_id, Task.title, Task),
    ]
    column_labels = {
        SubTask.task: "Task",
        SubTask.is_completed: "Completed",
    }
    export_types = ["csv", "json"]


class TagAdmin(ModelView, model=Tag):
    name = "Tag"
    name_plural = "Tags"
    category = "Tasks"
    icon = "fa-solid fa-tag"
    page_size = 25
    column_list = [
        Tag.id,
        Tag.user_id,
        Tag.name,
        Tag.color,
        Tag.is_user_tag,
        Tag.created_at,
    ]
    column_searchable_list = [Tag.name]
    column_sortable_list = [Tag.name, Tag.created_at]
    column_filters = [
        BooleanFilter(Tag.is_user_tag),
        ForeignKeyFilter(Tag.user_id, User.email, User),
    ]
    column_labels = {
        Tag.is_user_tag: "User tag",
    }
    form_columns = [
        Tag.name,
        Tag.color,
        Tag.user,
        Tag.is_user_tag,
        Tag.created_at,
        Tag.updated_at,
    ]
    export_types = ["csv", "json"]


class FriendRequestAdmin(ModelView, model=FriendRequest):
    name = "Friend request"
    name_plural = "Friend requests"
    category = "Friends"
    icon = "fa-solid fa-user-group"
    page_size = 25
    column_list = [
        FriendRequest.id,
        FriendRequest.requester_id,
        FriendRequest.addressee_id,
        FriendRequest.status,
        FriendRequest.created_at,
    ]
    column_sortable_list = [FriendRequest.status, FriendRequest.created_at]
    column_filters = [AllUniqueStringValuesFilter(FriendRequest.status)]
    export_types = ["csv", "json"]


class SyncEventAdmin(ModelView, model=SyncEvent):
    name = "Sync event"
    name_plural = "Sync events"
    category = "Sync"
    icon = "fa-solid fa-arrows-rotate"
    page_size = 25
    column_list = [
        SyncEvent.id,
        SyncEvent.user_id,
        SyncEvent.entity,
        SyncEvent.entity_id,
        SyncEvent.op,
        SyncEvent.occurred_at,
    ]
    column_searchable_list = [SyncEvent.entity, SyncEvent.op]
    column_sortable_list = [SyncEvent.occurred_at, SyncEvent.entity, SyncEvent.op]
    column_filters = [
        AllUniqueStringValuesFilter(SyncEvent.entity),
        AllUniqueStringValuesFilter(SyncEvent.op),
    ]
    export_types = ["csv", "json"]


class SyncOpAdmin(ModelView, model=SyncOp):
    name = "Sync op"
    name_plural = "Sync ops"
    category = "Sync"
    icon = "fa-solid fa-database"
    page_size = 25
    column_list = [
        SyncOp.id,
        SyncOp.user_id,
        SyncOp.op_id,
        SyncOp.device_id,
        SyncOp.created_at,
    ]
    column_sortable_list = [SyncOp.created_at]
    column_filters = [OperationColumnFilter(SyncOp.user_id)]
    export_types = ["csv", "json"]


def register_admin_views(admin) -> None:
    admin.add_view(UserAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(SubTaskAdmin)
    admin.add_view(TagAdmin)
    admin.add_view(FriendRequestAdmin)
    admin.add_view(SyncEventAdmin)
    admin.add_view(SyncOpAdmin)
