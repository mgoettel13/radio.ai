from fastapi import FastAPI
from sqladmin import Admin, ModelView

from app.database import engine
from app.models import Article, Summary, User, UserArticle


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.is_active, User.is_superuser]
    column_searchable_list = [User.email]
    column_sortable_list = [User.email, User.is_active, User.is_verified]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class ArticleAdmin(ModelView, model=Article):
    column_list = [
        Article.id,
        Article.title,
        Article.published_at,
        Article.author,
        Article.category,
        Article.fetched_at
    ]
    column_searchable_list = [Article.title, Article.author, Article.category]
    column_sortable_list = [Article.published_at, Article.fetched_at, Article.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class SummaryAdmin(ModelView, model=Summary):
    column_list = [
        Summary.id,
        Summary.article_id,
        Summary.model_used,
        Summary.tokens_used,
        Summary.created_at
    ]
    column_sortable_list = [Summary.created_at, Summary.tokens_used]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class UserArticleAdmin(ModelView, model=UserArticle):
    column_list = [
        UserArticle.id,
        UserArticle.user_id,
        UserArticle.article_id,
        UserArticle.is_read,
        UserArticle.is_favorite,
        UserArticle.read_at
    ]
    column_sortable_list = [UserArticle.is_read, UserArticle.is_favorite, UserArticle.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


def setup_admin(app: FastAPI) -> Admin:
    """Setup SQLAdmin for the FastAPI app."""
    admin = Admin(app, engine)

    admin.add_view(UserAdmin)
    admin.add_view(ArticleAdmin)
    admin.add_view(SummaryAdmin)
    admin.add_view(UserArticleAdmin)

    return admin
