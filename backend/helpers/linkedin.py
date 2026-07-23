from django.contrib.auth import get_user_model
import logging
import requests

logger = logging.getLogger(__name__)

User = get_user_model()
def UserNotConnectedLinkedIn(Exception):
    pass

class LinkedInShareError(Exception):
    pass
def get_linkedin_user_details(user):
    try:
        linkedin_social = user.socialaccount_set.get(provider="linkedin")
    except user.socialaccount_set.model.DoesNotExist:
        raise UserNotConnectedLinkedIn("LinkedIn is not connected on this user.")
    return linkedin_social

def get_share_headers(linkedin_social):
    tokens = linkedin_social.socialtoken_set.all()
    if not tokens.exists():
        raise LinkedInShareError("LinkedIn connection is invalid. Please login again.")
    social_token = tokens.first()
    return {
        "Authorization": f"Bearer {social_token.token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }


def share_to_linkedin(user, text: str) -> str:
    if not user.socialaccount_set.filter(provider="linkedin").exists():
        raise UserNotConnectedLinkedIn("User is not linked to LinkedIn")

    linkedin_social = user.socialaccount_set.get(provider="linkedin")
    linkedin_user_id = linkedin_social.uid

    
    if not linkedin_user_id:
        raise LinkedInShareError("Invalid LinkedIn User ID")
    headers = get_share_headers(linkedin_social)
    endpoint = "https://api.linkedin.com/v2/ugcPosts"
    payload = {
        "author": f"urn:li:person:{linkedin_user_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    response = requests.post(endpoint, json=payload, headers=headers)
    response.raise_for_status()

    post_urn = response.headers.get("x-restli-id", "")
    if not post_urn:
        raise LinkedInShareError("LinkedIn returned no post URN")

    logger.info("LinkedIn post created (urn=%s)", post_urn)
    return post_urn
