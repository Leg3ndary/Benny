from typing import Optional

from bTagScript import Block, Context, helper_parse_if


class DeleteBlock(Block):
    """
    Delete block, deletes if the given parameter is true
    """

    ACCEPTED_NAMES = ("delete", "del")

    def will_accept(self, ctx: Context) -> bool:
        """
        will accept
        """
        dec = ctx.verb.declaration.lower()
        return any([dec == "delete", dec == "del"])

    def process(self, ctx: Context) -> Optional[str]:
        """
        process the delete
        """
        if "delete" in ctx.response.actions.keys():
            return None
        if ctx.verb.parameter is None:
            value = True
        else:
            value = helper_parse_if(ctx.verb.parameter)
        ctx.response.actions["delete"] = value
        return ""
