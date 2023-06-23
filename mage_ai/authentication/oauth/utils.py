from datetime import datetime
from typing import List

from mage_ai.orchestration.db.models.oauth import Oauth2AccessToken, Oauth2Application


def access_tokens_for_provider(provider: str) -> List[Oauth2AccessToken]:
    if oauth_client := Oauth2Application.query.filter(
        Oauth2Application.client_id == provider,
    ).first():
        access_tokens = Oauth2AccessToken.query.filter(
            Oauth2AccessToken.expires > datetime.utcnow(),
            Oauth2AccessToken.oauth2_application_id == oauth_client.id,
        )
    else:
        access_tokens = []
    return list(access_tokens)
