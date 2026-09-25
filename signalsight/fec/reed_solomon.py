import numpy as np
import reedsolo

class ReedSolomonFEC:
    """
    Reed-Solomon FEC Encoder/Decoder using reedsolo.
    Operates on bytes (arrays of uint8).
    """
    def __init__(self, nsym: int = 32):
        """
        Initialize RS codec.
        nsym: number of ECC symbols (bytes) per block.
        """
        self.nsym = nsym
        self.codec = reedsolo.RSCodec(nsym)
        
    def encode_bytes(self, data: np.ndarray) -> np.ndarray:
        """
        Encode an array of bytes.
        """
        data_bytes = bytearray(data.tolist())
        encoded = self.codec.encode(data_bytes)
        return np.array(list(encoded), dtype=np.uint8)
        
    def decode_bytes(self, data: np.ndarray) -> tuple[np.ndarray, int, int]:
        """
        Decode an array of bytes.
        Returns: (decoded_data, num_errors_corrected, num_erasures_corrected)
        """
        data_bytes = bytearray(data.tolist())
        try:
            decoded, decoded_full, errata_pos = self.codec.decode(data_bytes)
            num_errs = len(errata_pos) if errata_pos else 0
            return np.array(list(decoded), dtype=np.uint8), num_errs, 0
        except reedsolo.ReedSolomonError:
            # Decoding failed
            return np.array([], dtype=np.uint8), -1, -1

    def encode_bits(self, bits: np.ndarray) -> np.ndarray:
        """
        Helper: Pack bits to bytes, encode, and unpack to bits.
        """
        pad = (8 - len(bits) % 8) % 8
        padded = np.pad(bits, (0, pad), 'constant')
        byte_data = np.packbits(padded)
        encoded_bytes = self.encode_bytes(byte_data)
        encoded_bits = np.unpackbits(encoded_bytes)
        return encoded_bits
        
    def decode_bits(self, bits: np.ndarray, original_bit_len: int = None) -> np.ndarray:
        """
        Helper: Pack bits to bytes, decode, and unpack.
        """
        # Truncate to multiple of 8 if needed
        rem = len(bits) % 8
        if rem != 0:
            bits = bits[:-rem]
            
        byte_data = np.packbits(bits)
        decoded_bytes, errs, _ = self.decode_bytes(byte_data)
        if errs == -1:
            return np.array([], dtype=np.uint8)
            
        decoded_bits = np.unpackbits(decoded_bytes)
        if original_bit_len is not None and original_bit_len < len(decoded_bits):
            decoded_bits = decoded_bits[:original_bit_len]
            
        return decoded_bits
