from typing import Optional, Union
from flask import Response, render_template, flash, redirect, request

def handle_errors_and_redirect(
    error_message: str,
    category: str = 'danger',
    redirect_url: Optional[str] = None
) -> Union[Response, render_template]:
    """
    A function to handle errors and redirect the user.
    
    Note: This function assumes that flash() and redirect() are available 
    in the calling context/module.

    Parameters
    ----------
    error_message : str
        The error message to be displayed to the user.
    category : str, optional
        The category of the error message, by default 'danger'.
    redirect_url : Optional[str], optional
        The URL to redirect the user to, by default None.

    Returns
    -------
    Union[Response, render_template]
        A Response or render_template object, depending on whether a redirect URL was provided.
    """
    flash(error_message, category)
    return redirect(redirect_url) if redirect_url else render_template(request.endpoint.split('.')[-1] + '.html')