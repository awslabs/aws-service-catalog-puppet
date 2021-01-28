def slugify_for_cloudformation_stack_name(raw) -> str:
    return raw.replace("_", "-")
