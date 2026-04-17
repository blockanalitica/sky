async def chunk_generator_by_key(iterator, chunk_size, key_func):
    """
    Yield successive chunks from the iterable.
    Ensures that items with the same 'key_func' value are kept in the same chunk.
    Preserves the original order!

    :param iterable: The input iterable or generator
    :param chunk_size: The target chunk size (chunks may be slightly larger or smaller)
    :param key_func: A function that extracts the key to check for duplicated values
    """
    current_chunk = []
    previous_key = None

    async for item in iterator:
        # Get the key for the current item (for example, duplicated field)
        current_key = key_func(item)

        # If chunk has reached size limit AND the key changes, yield the current chunk
        if len(current_chunk) >= chunk_size and current_key != previous_key:
            yield current_chunk
            current_chunk = []

        # Add the current item to the chunk
        current_chunk.append(item)
        previous_key = current_key

    # Yield the final chunk if it's not empty
    if current_chunk:
        yield current_chunk
