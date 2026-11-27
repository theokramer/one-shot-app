"""Make provider requests without forwarding credentials or files across redirects."""
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


open_request = urllib.request.build_opener(NoRedirect()).open
