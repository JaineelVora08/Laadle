from rest_framework.views import APIView


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Input:  { name, email, password, role, current_level }
    Output: AuthTokenResponse
    Calls:  Nothing
    """
    def post(self, request):
        pass


class LoginView(APIView):
    """
    POST /api/auth/login/
    Input:  { email, password }
    Output: AuthTokenResponse { access, refresh, user_id, role }
    Calls:  Nothing
    """
    def post(self, request):
        pass


class TokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    Input:  { refresh }
    Output: { access }
    """
    def post(self, request):
        pass


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token.
    """
    def post(self, request):
        pass
