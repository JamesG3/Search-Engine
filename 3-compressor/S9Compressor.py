S_9 = 0x90000000
S_8 = 0x80000000
S_7 = 0x70000000
S_6 = 0x60000000
S_5 = 0x50000000
S_4 = 0x40000000
S_3 = 0x30000000
S_2 = 0x20000000
S_1 = 0x10000000


def encoder(data, length):
	# [volume, maxValue, simple(initControlbits), shift(occupyBits)]
	encodeSET = [[28, 1, S_9, 1],
			[14, 3, S_8, 2],
			[9, 7, S_7, 3],
			[7, 15, S_6, 4],
			[5, 31, S_5, 5],
			[4, 127, S_4, 7],
			[3, 511, S_3, 9],
			[2, 16383, S_2, 14],
			[1, 268435455, S_1, 28]]
	offset = 0
	res = []
	while offset < length:
		for SET in encodeSET:
			volume, maxValue, simple, shift = SET[0], SET[1], SET[2], SET[3]
			if (offset+volume <= length) and max(data[offset:offset+volume]) <= maxValue:
				tmp = data[offset]
				for i in xrange(1, volume):
					tmp |= ((data[offset+i]) << (shift*i))
				res.append(tmp | simple)
				offset += volume
				break
	return res


def decoder(data):
	# [volume, bit, shift]
	decodeSET = {S_9: [28, 0x1, 1],
				S_8: [14, 0x3, 2],
				S_7: [9, 0x7, 3],
				S_6: [7, 0xf, 4],
				S_5: [5, 0x1f, 5],
				S_4: [4, 0x7f, 7],
				S_3: [3, 0x1ff, 9],
				S_2: [2, 0x3fff,14],
				S_1: [1, 0xfffffff,28]}
	res = []
	for a in data:
		code = a & 0xf0000000
		data = a & 0xfffffff
		SET = decodeSET[code]
		volume, bit, shift = SET[0], SET[1], SET[2]
		for i in xrange(volume):
			res.append(data & bit)
			data >>= shift
	return res





