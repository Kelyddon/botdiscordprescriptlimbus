"""Implémentation de repli pour un sous-ensemble des fonctions `audioop`.

Implémente uniquement ce dont `discord.player` a besoin (principalement `mul`).
Ce repli pur Python évite de dépendre au module C `audioop` déprécié sur les versions récentes.
"""
from __future__ import annotations
import array
from typing import ByteString


def _clip16(v: int) -> int:
	"""Saturation signed 16-bit."""
    if v > 32767:
        return 32767
    if v < -32768:
        return -32768
    return v


def mul(fragment: ByteString, width: int, factor: float) -> bytes:
    """Multiplie les échantillons de `fragment` par `factor`.

    Supporte les échantillons 16 bits (`width == 2`). Pour d'autres largeurs,
    une approximation simple est utilisée (8 bits) ou `NotImplementedError` est levée.
    """
    if width == 2:
		# Cas principal: PCM 16-bit signed little-endian (usage courant Discord).
        arr = array.array('h')
        # frombytes requires a bytes-like object
        arr.frombytes(bytes(fragment))
        if factor == 1.0:
            return arr.tobytes()
        for i in range(len(arr)):
			# Multiplication + saturation pour éviter le wrap numérique.
            val = int(round(arr[i] * factor))
            arr[i] = _clip16(val)
        return arr.tobytes()

    if width == 1:
		# 8-bit souvent non signé: conversion autour de 0x80 puis re-bias.
        b = bytearray(fragment)
        for i in range(len(b)):
            signed = b[i] - 128
            val = int(round(signed * factor))
            # clip to signed 8-bit
            if val > 127:
                val = 127
            if val < -128:
                val = -128
            b[i] = (val + 128) & 0xFF
        return bytes(b)

    raise NotImplementedError(f"Le repli audioop.mul ne supporte pas width={width}")


__all__ = ["mul"]
