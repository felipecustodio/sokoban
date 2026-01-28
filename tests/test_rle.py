"""Tests for RLE encoding/decoding."""

from sokoban_engine.io.rle import decode_rle, encode_rle, is_rle_format


class TestDecodeRLE:
    """Tests for decode_rle function."""

    def test_simple_decode(self):
        """Test decoding a simple RLE string."""
        # Note: The example from docs has a space, let's test without
        rle = "4#|#@$.#|4#"
        result = decode_rle(rle)
        assert result == "####\n#@$.#\n####"

    def test_decode_with_counts(self):
        """Test decoding with various run counts."""
        rle = "7#|#.@-#-#|#$*-$-#|7#"
        result = decode_rle(rle)
        lines = result.split("\n")
        assert lines[0] == "#######"
        assert lines[1] == "#.@ # #"

    def test_decode_hyphen_to_space(self):
        """Test that hyphens are converted to spaces."""
        rle = "3#|#-@-#|3#"
        result = decode_rle(rle)
        assert " @ " in result

    def test_decode_underscore_to_space(self):
        """Test that underscores are converted to spaces."""
        rle = "3#|#_@_#|3#"
        result = decode_rle(rle)
        assert " @ " in result

    def test_decode_no_count(self):
        """Test decoding without run counts (count = 1)."""
        rle = "###|#@#|###"
        result = decode_rle(rle)
        assert result == "###\n#@#\n###"

    def test_decode_multiline_rle(self):
        """Test decoding RLE that spans multiple lines."""
        rle = "4#|\n#@$.#|\n4#"
        result = decode_rle(rle)
        assert result == "####\n#@$.#\n####"


class TestEncodeRLE:
    """Tests for encode_rle function."""

    def test_simple_encode(self):
        """Test encoding a simple level."""
        level = "####\n#@$.#\n####"
        result = encode_rle(level)
        assert result == "4#|#@$.#|4#"

    def test_encode_with_spaces(self):
        """Test encoding converts spaces to hyphens."""
        level = "###\n# @#\n###"
        result = encode_rle(level)
        # Space becomes hyphen
        assert "-@" in result

    def test_encode_with_underscore(self):
        """Test encoding with underscore option."""
        level = "###\n# @#\n###"
        result = encode_rle(level, use_hyphen=False)
        # Space becomes underscore
        assert "_@" in result

    def test_encode_strips_trailing_spaces(self):
        """Test that trailing spaces are stripped."""
        level = "###  \n#@$  \n###  "
        result = encode_rle(level)
        # Should not have trailing hyphens
        assert not result.endswith("-")

    def test_encode_consecutive_chars(self):
        """Test encoding consecutive identical characters."""
        level = "######\n#    #\n######"
        result = encode_rle(level)
        assert "6#" in result
        assert "4-" in result


class TestIsRLEFormat:
    """Tests for is_rle_format function."""

    def test_rle_with_pipe(self):
        """Test detection of RLE with pipe separators."""
        assert is_rle_format("4#|#@$.#|4#")

    def test_rle_with_digits(self):
        """Test detection of RLE with digit prefixes."""
        assert is_rle_format("4#3#2#")

    def test_xsb_format(self):
        """Test that standard XSB format is not detected as RLE."""
        level = "####\n#@$.#\n####"
        assert not is_rle_format(level)

    def test_single_line_rle(self):
        """Test detection of single-line RLE."""
        assert is_rle_format("7#")


class TestRoundtrip:
    """Test encoding then decoding returns equivalent level."""

    def test_roundtrip_simple(self):
        """Test encode->decode roundtrip."""
        original = "####\n#@$.#\n####"
        encoded = encode_rle(original)
        decoded = decode_rle(encoded)
        # After roundtrip, should be equivalent (spaces may differ)
        assert decoded.replace("-", " ") == original.replace("-", " ")

    def test_roundtrip_complex(self):
        """Test roundtrip with a more complex level."""
        original = """#######
#.@ # #
#$* $ #
#   $ #
# ..  #
#  *  #
#######"""
        encoded = encode_rle(original)
        decoded = decode_rle(encoded)
        # Lines should match (ignoring trailing spaces)
        orig_lines = [line.rstrip() for line in original.split("\n")]
        dec_lines = [line.rstrip() for line in decoded.split("\n")]
        assert orig_lines == dec_lines
