class InternalDomainClient:
    """
    Used internally to interact with domain management service.
    """

    def get_user_domains(self, user_id: str) -> list:
        """
        GET /internal/domains/user/<user_id>/
        Returns: list of DomainLinkResponse dicts
        """
        pass

    def get_domain(self, domain_id: str) -> dict:
        """
        GET /internal/domains/<domain_id>/
        Returns: DomainNode dict
        """
        pass
