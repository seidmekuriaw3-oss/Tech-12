from database.db import get_db
import logging
logger = logging.getLogger(__name__)


class AdService:
    """Service class for advertisement management"""
    
    @staticmethod
    def get_all():
        """
        Get all advertisements (including inactive) for admin panel.
        
        Returns:
            list: All ads ordered by ID descending
        """
        try:
            db = get_db()
            return db.execute("SELECT * FROM advertisements ORDER BY id DESC").fetchall()
        except Exception as e:
            logger.error(f"Error getting all ads: {e}")
            return []
    
    @staticmethod
    def get_all_admin():
        """
        Alias for get_all() - get all ads for admin panel.
        
        Returns:
            list: All ads ordered by ID descending
        """
        return AdService.get_all()
    
    @staticmethod
    def get_active():
        """
        Get only active advertisements for customer display.

        Returns:
            list: Active ads ordered by sort_order
        """
        try:
            db = get_db()
            return db.execute(
                """SELECT id, title, title_am, title_ar,
                          description, description_am, description_ar,
                          image, media_url, link, sort_order, start_date, end_date
                   FROM advertisements
                   WHERE is_active = 1
                   AND (end_date IS NULL OR end_date > NOW())
                   AND (start_date IS NULL OR start_date <= NOW())
                   ORDER BY sort_order ASC, id DESC"""
            ).fetchall()
        except Exception as e:
            logger.error(f"Error getting active ads: {e}")
            return []
    
    @staticmethod
    def get_by_id(aid):
        """
        Get a single advertisement by ID.
        
        Args:
            aid (int): Advertisement ID
        
        Returns:
            dict or None: Ad data if found, None otherwise
        """
        try:
            db = get_db()
            return db.execute("SELECT * FROM advertisements WHERE id = %s", (aid,)).fetchone()
        except Exception as e:
            logger.error(f"Error getting ad by ID {aid}: {e}")
            return None
    
    @staticmethod
    def create(data):
        """
        Create a new advertisement.
        
        Args:
            data (dict): Ad data with keys:
                - text (str): Advertisement text (required)
                - title (str): Ad title (optional)
                - title_am (str): Amharic title (optional)
                - title_ar (str): Arabic title (optional)
                - description (str): Ad description (optional)
                - description_am (str): Amharic description (optional)
                - description_ar (str): Arabic description (optional)
                - image (str): Media file path (optional)
                - link (str): Ad link URL (optional)
                - sort_order (int): Display order (default: 0)
                - start_date (str): Start date (optional)
                - end_date (str): End date (optional)
        
        Returns:
            int or None: New ad ID if successful, None otherwise
        """
        try:
            db = get_db()
            cursor = db.execute(
                """INSERT INTO advertisements (
                    title, title_am, title_ar, 
                    description, description_am, description_ar,
                    image, link, sort_order, is_active, start_date, end_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s)
                RETURNING id""",
                (
                    data.get('title', ''),
                    data.get('title_am', ''),
                    data.get('title_ar', ''),
                    data.get('description', data.get('text', '')),
                    data.get('description_am', ''),
                    data.get('description_ar', ''),
                    data.get('image', data.get('media', '')),
                    data.get('link', ''),
                    data.get('sort_order', 0),
                    data.get('start_date'),
                    data.get('end_date')
                )
            )
            db.commit()
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error creating ad: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def update(aid, data):
        """
        Update an existing advertisement.
        
        Args:
            aid (int): Advertisement ID
            data (dict): Ad data with keys:
                - title, title_am, title_ar
                - description, description_am, description_ar
                - image, link, sort_order, is_active
                - start_date, end_date
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute(
                """UPDATE advertisements SET 
                    title=%s, title_am=%s, title_ar=%s, 
                    description=%s, description_am=%s, description_ar=%s,
                    image=%s, link=%s, sort_order=%s, is_active=%s,
                    start_date=%s, end_date=%s, updated_at=CURRENT_TIMESTAMP
                   WHERE id=%s""",
                (
                    data.get('title', ''),
                    data.get('title_am', ''),
                    data.get('title_ar', ''),
                    data.get('description', data.get('text', '')),
                    data.get('description_am', ''),
                    data.get('description_ar', ''),
                    data.get('image', data.get('media', '')),
                    data.get('link', ''),
                    data.get('sort_order', 0),
                    data.get('is_active', 1),
                    data.get('start_date'),
                    data.get('end_date'),
                    aid
                )
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating ad {aid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def delete(aid):
        """
        Delete an advertisement by ID.
        
        Args:
            aid (int): Advertisement ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute("DELETE FROM advertisements WHERE id = %s", (aid,))
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting ad {aid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def toggle_active(aid):
        """
        Toggle advertisement active status (activate/deactivate).
        
        Args:
            aid (int): Advertisement ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute(
                "UPDATE advertisements SET is_active = 1 - is_active, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (aid,)
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error toggling ad {aid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def activate(aid):
        """
        Activate an advertisement.
        
        Args:
            aid (int): Advertisement ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute(
                "UPDATE advertisements SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (aid,)
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error activating ad {aid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def deactivate(aid):
        """
        Deactivate an advertisement.
        
        Args:
            aid (int): Advertisement ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute(
                "UPDATE advertisements SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (aid,)
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deactivating ad {aid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def update_sort_order(aid, sort_order):
        """
        Update the display order of an advertisement.
        
        Args:
            aid (int): Advertisement ID
            sort_order (int): New sort order value
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute(
                "UPDATE advertisements SET sort_order = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (sort_order, aid)
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating sort order for ad {aid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_count():
        """
        Get total number of advertisements.
        
        Returns:
            int: Total ad count
        """
        try:
            db = get_db()
            result = db.execute("SELECT COUNT(*) FROM advertisements").fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting ad count: {e}")
            return 0
    
    @staticmethod
    def get_active_count():
        """
        Get number of active advertisements.
        
        Returns:
            int: Active ad count
        """
        try:
            db = get_db()
            result = db.execute("SELECT COUNT(*) FROM advertisements WHERE is_active = 1").fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting active ad count: {e}")
            return 0