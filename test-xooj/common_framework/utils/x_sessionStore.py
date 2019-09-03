import logging

from django.contrib.sessions.backends.cached_db import SessionStore as originSessionStore
from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from django.utils.encoding import force_text


class SessionStore(originSessionStore):
    def create_model_instance(self, data):
        """
        Return a new instance of the session model object, which represents the
        current session state. Intended to be used for saving the session data
        to the database.
        """
        m = self.model(
            session_key=self._get_or_create_session_key(),
            session_data=self.encode(data),
            expire_date=self.get_expiry_date(),
        )

        ip = getattr(self, 'ip', None)
        if ip:
            setattr(m, 'ip', ip)

        return m

    @classmethod
    def get_model_class(cls):
        # Avoids a circular import and allows importing SessionStore when
        # django.contrib.sessions is not in INSTALLED_APPS.
        from common_auth.models import XSession
        return XSession

    def load(self):
        try:
            data = self._cache.get(self.cache_key)
        except Exception as e:
            # Some backends (e.g. memcache) raise an exception on invalid
            # cache keys. If this happens, reset the session. See #17810.
            data = None

        if data is None:
            # Duplicate DBStore.load, because we need to keep track
            # of the expiry date to set it properly in the cache.
            try:
                s = self.model.objects.get(
                    session_key=self.session_key,
                    expire_date__gt=timezone.now()
                )
                data = self.decode(s.session_data)
                data['ip'] = s.ip
                self._cache.set(self.cache_key, data, self.get_expiry_age(expiry=s.expire_date))
            except (self.model.DoesNotExist, SuspiciousOperation) as e:
                if isinstance(e, SuspiciousOperation):
                    logger = logging.getLogger('django.security.%s' % e.__class__.__name__)
                    logger.warning(force_text(e))
                self._session_key = None
                data = {}
        return data
