from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from streamrip.metadata import TrackMetadata

import sys

class Matcher():

    def __init__(self, meta, pure_only=True):
        self.metadata = meta
        self.pure_only = True

    def _valid(self, proposed):
        threshold = 85
        original = self.metadata

        score = 0

        illegal_album_parts = ["tribute", "live"]

        for iap in illegal_album_parts:
            if (iap in proposed.album.lower() and 
                (original.album == None or iap not in original.album.lower())):
                return score

        p_artists = [proposed.artist]
        if hasattr(proposed, "albumartist") and proposed.albumartist != None:
            if (proposed.albumartist == "Various Artists"):
                return score
            p_artists.append(proposed.albumartist)

        extract_res = process.extract(original.artist, p_artists, limit=1)
        if (len(extract_res) == 0 or extract_res[0][1] < threshold):
            return score
        
        for a in p_artists:
            if ("tribute" in a.lower() and "tribute" not in original.artist.lower()):
                return score

        score += extract_res[0][1] 

        if ("style of" in proposed.title.casefold()):
            return score

        extract_res = process.extract(original.title, [proposed.title], limit=1)
        if (len(extract_res) != 0 and extract_res[0][1] >= threshold):
            score += extract_res[0][1]

        if ("version" in proposed.title.lower() and self.metadata.version == None):
            return score
        
        if ("Live" in proposed.title and (original.version == None or "Live" not in original.version)):
            return score
        
        if (hasattr(original, "explicit") and hasattr(proposed, "explicit")):
            if (original.explicit == proposed.explicit):
                score += 10

        if (original.version == proposed.version):
            score += 40

        if (hasattr(original, "isrc") and hasattr(proposed, "isrc") and original.isrc == proposed.isrc):
            score += 100

        return score
    

    def csv(obj) -> str:
        result = ""
        for x in dir(obj):
            c = getattr(obj.meta, x)
            if (c == None):
                result += ","
            else:
                result += str(getattr(obj, x)).replace(",", "") + ","
        if (result.endswith(",")):
            result = result[:-1] + "\n"
        return result
    
    def compare(self, list):
        candidates = []
        artists = {}
        for item in list:
            t = item.meta

            if (self.pure_only and t.version != None):
                continue

            score = self._valid(t)

            if (score >= 150):
                if (t.albumartist != "Various Artists" and t.albumartist not in artists):
                    artists[t.albumartist] = 1
                else:
                    artists[t.albumartist] += 1
                candidates.append((item, score))

        max_bias = 0
        winner = None
        for item, score in candidates:
            bias = 0
            t = item.meta

            bias += score
            bias += 100 * artists[t.albumartist]
            if(t.bit_depth != None):
                bias += 0.05 * t.bit_depth
            if(t.sampling_rate != None):
                temp = t.sampling_rate
                if (temp > 1000):
                    temp /= 1000
                bias += temp

            if (bias > max_bias):
                winner = item
                max_bias = bias

            # break ties by picking one with less tracks
            # elif(bias == max_bias):
            #     if(winner == None or t.tracktotal < winner.meta.tracktotal):
            #         winner = item
            #         max_bias = bias

            #print(t.title, t.artist, t.album, t.tracktotal, t.albumartist, t.genre, t.bit_depth, t.sampling_rate, t.date, t.version, score, bias, "\n", sep=",")

        return winner