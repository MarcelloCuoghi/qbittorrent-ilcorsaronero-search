if __name__ == "__main__":
    from ilcorsaronero import ilcorsaronero
    from helpers import retrieve_url

    # Create an instance of the ilcorsaronero class
    corsaro = ilcorsaronero()

    # Try searching a torrent
    try:
        corsaro.search('Inception', cat='movies')
    except Exception as e:
        print(f"An error occurred: {e}")