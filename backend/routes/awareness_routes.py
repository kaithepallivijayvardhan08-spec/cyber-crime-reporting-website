from flask import Blueprint, jsonify, request

from database.db_connection import db


awareness_bp = Blueprint('awareness', __name__)


@awareness_bp.route('/articles', methods=['GET'])
def get_articles():
    """Return public awareness articles, optionally filtered by category."""
    category = request.args.get('category')
    if category is not None:
        category = category.strip()
        if not category or len(category) > 50:
            return jsonify({'error': 'Invalid article category'}), 400

    query = """
        SELECT id, title, content, category, image_url, author, views,
               is_featured, created_at
        FROM awareness_articles
    """
    params = ()
    if category:
        query += " WHERE category = %s"
        params = (category,)
    query += " ORDER BY is_featured DESC, created_at DESC, id DESC"

    try:
        return jsonify({'articles': db.execute_query(query, params)}), 200
    except Exception:
        return jsonify({'error': 'Unable to load awareness articles'}), 503


@awareness_bp.route('/article/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """Return one public awareness article by its numeric ID."""
    try:
        articles = db.execute_query(
            """SELECT id, title, content, category, image_url, author, views,
                      is_featured, created_at
               FROM awareness_articles WHERE id = %s""",
            (article_id,)
        )
    except Exception:
        return jsonify({'error': 'Unable to load awareness article'}), 503

    if not articles:
        return jsonify({'error': 'Article not found'}), 404
    return jsonify({'article': articles[0]}), 200
