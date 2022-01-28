## Typing support 
from typing import *
from numpy.typing import ArrayLike 

## Module imports
import numpy as np
import math
import numbers 
import scipy.sparse as sps

## Function/structure imports
from scipy.sparse import coo_matrix, csc_matrix
from array import array
from itertools import combinations
from scipy.special import binom
from scipy.spatial.distance import pdist


# def boundary_matrix(S: Iterable, F: Iterable):
#   """
#   Creates a p-boundary matrix (CSC format) from an iterable of simplices.

#   Assumes S only enumerates p-simplices.

#   Parameters:
#     S := Iterable over p-simplices
#     F := Iterable over (p-1)-faces
#   """ 
#   array('I')

def rank_C2(i: int, j: int, n: int):
  i, j = (j, i) if j < i else (i, j)
  return(int(n*i - i*(i+1)/2 + j - i - 1))

def unrank_C2(x: int, n: int):
  i = int(n - 2 - np.floor(np.sqrt(-8*x + 4*n*(n-1)-7)/2.0 - 0.5))
  j = int(x + i + 1 - n*(n-1)/2 + (n-i)*((n-i)-1)/2)
  return(i,j) 

def H1_boundary_matrix(vertices: ArrayLike, edges: Iterable, coboundary: bool = False, dtype = int):
  p = np.argsort(vertices)        ## inverse permutation 
  v_sort = np.array(vertices)[p]  ## use p for log(n) lookup 
  V, E = len(vertices), len(edges)
  
  data_val, row_ind, col_ind = np.zeros(2*E, dtype=dtype), np.zeros(2*E, dtype=int), np.zeros(2*E, dtype=int)
  for i, (u,v) in enumerate(edges):
    u_ind, v_ind = np.searchsorted(v_sort, [u, v])
    data_val[2*i], data_val[2*i+1] = -1, 1
    row_ind[2*i], row_ind[2*i+1] = int(p[u_ind]), int(p[v_ind])
    col_ind[2*i], col_ind[2*i+1] = int(i), int(i)
  D = csc_matrix((data_val, (row_ind, col_ind)), shape=(V, E), dtype=dtype)
  
  ## TODO: make coboundary computation more efficient 
  if coboundary:
    D = csc_matrix(np.flipud(np.fliplr(D.A)).T)
  return(D)

def H2_boundary_matrix(edges: Iterable, triangles: Iterable, coboundary: bool = False, N = "max", dtype = int):
  if N == "max": N = np.max(np.array(edges).flatten())

  E_ranks = np.array([rank_C2(u, v, N) for (u,v) in edges], dtype=int)
  p = np.argsort(E_ranks)        ## inverse permutation 
  E_sort = E_ranks[p]  ## use p for log(n) lookup 
  E, T = len(E_ranks), len(triangles) # todo: fix 
  
  data_val, row_ind, col_ind = np.zeros(3*T, dtype=dtype), np.zeros(3*T, dtype=int), np.zeros(3*T, dtype=int)
  for i, (u,v,w) in enumerate(triangles):
    uv_ind, uw_ind, vw_ind = np.searchsorted(E_sort, [rank_C2(u, v, N), rank_C2(u, w, N), rank_C2(v, w, N)])
    data_val[3*i], data_val[3*i+1], data_val[3*i+2] = 1, -1, 1
    row_ind[3*i], row_ind[3*i+1], row_ind[3*i+2] = int(p[uv_ind]), int(p[uw_ind]), int(p[vw_ind])
    col_ind[3*i], col_ind[3*i+1], col_ind[3*i+2] = int(i), int(i), int(i)
  D = csc_matrix((data_val, (row_ind, col_ind)), shape=(E, T), dtype=dtype)
  
  ## TODO: make coboundary computation more efficient 
  if coboundary:
    D = csc_matrix(np.flipud(np.fliplr(D.A)).T)
  return(D)


def inverse_choose(x: int, k: int):
	assert k >= 1, "k must be >= 1" 
	if k == 1: return(x)
	if k == 2:
		rng = np.array(list(range(int(np.floor(np.sqrt(2*x))), int(np.ceil(np.sqrt(2*x)+2) + 1))))
		final_n = rng[np.nonzero(np.array([math.comb(n, 2) for n in rng]) == x)[0].item()]
	else:
		# From: https://math.stackexchange.com/questions/103377/how-to-reverse-the-n-choose-k-formula
		if x < 10**7:
			lb = (math.factorial(k)*x)**(1/k)
			potential_n = np.array(list(range(int(np.floor(lb)), int(np.ceil(lb+k)+1))))
			idx = np.nonzero(np.array([math.comb(n, k) for n in potential_n]) == x)[0].item()
			final_n = potential_n[idx]
		else:
			lb = np.floor((4**k)/(2*k + 1))
			C, n = math.factorial(k)*x, 1
			while n**k < C: n = n*2
			m = (np.nonzero( np.array(list(range(1, n+1)))**k >= C )[0])[0].item()
			potential_n = np.array(list(range(int(np.max([m, 2*k])), int(m+k+1))))
			ind = np.nonzero(np.array([math.comb(n, k) for n in potential_n]) == x)[0].item()
			final_n = potential_n[ind]
	return(final_n)

def is_distance_matrix(x: ArrayLike) -> bool:
	''' Checks whether 'x' is a distance matrix, i.e. is square, symmetric, and that the diagonal is all 0. '''
	x = np.array(x, copy=False)
	is_square = x.ndim == 2	and (x.shape[0] == x.shape[1])
	return(False if not(is_square) else np.all(np.diag(x) == 0))

def is_pairwise_distances(x: ArrayLike) -> bool:
	''' Checks whether 'x' is a 1-d array of pairwise distances '''
	x = np.array(x, copy=False) # don't use asanyarray here
	if x.ndim > 1: return(False)
	n = inverse_choose(len(x), 2)
	return(x.ndim == 1 and n == int(n))

def is_point_cloud(x: ArrayLike) -> bool: 
	''' Checks whether 'x' is a 2-d array of points '''
	return(isinstance(x, np.ndarray) and x.ndim == 2)

def as_dist_matrix(x: ArrayLike, metric="euclidean") -> ArrayLike:
	if is_pairwise_distances(x):
		n = inverse_choose(len(x), 2)
		assert n == int(n)
		D = np.zeros(shape=(n, n))
		D[np.triu_indices(n, k=1)] = x
		D = D.T + D
		return(D)
	elif is_distance_matrix(x):
		return(x)
	else:
		raise ValueError("x should be a distance matrix or a set of pairwise distances")

def is_dist_like(x: ArrayLike):
	return(is_distance_matrix(x) or is_pairwise_distances(x))

def is_index_like(x: ArrayLike):
	return(np.all([isinstance(el, numbers.Integral) for el in x]))

def enclosing_radius(a: ArrayLike) -> float:
	''' Returns the smallest 'r' such that the Rips complex on the union of balls of radius 'r' is contractible to a point. '''
	assert is_distance_matrix(a)
	return(np.min(np.amax(a, axis = 0)))

def rips(X: ArrayLike, r: float = np.inf, d: int = 1):
  ''' 
  Returns dictionary containing simplices and possibly weights of Rips d-complex of point cloud 'X' up to dimension 'd'.

  Parameters: 
    X := point cloud data 
    r := radius parameter for the Rips complex
  '''
  N, D = X.shape[0], pdist(X) 
  if r == np.inf:
    r = enclosing_radius(as_dist_matrix(D))
  rank_tri = lambda T : np.array([rank_C2(T[0],T[1],N), rank_C2(T[0],T[2],N), rank_C2(T[1],T[2],N)])
  Vertices, Edges, Triangles = np.arange(N, dtype=int), np.array([], dtype=int), array('I')
  if d >= 1:
    Edges = np.flatnonzero(D <= r*2)
    if d >= 2 and len(Edges) > 0:
      for T in combinations(range(N), 3):
        e_ranks = rank_tri(T)
        ind = np.searchsorted(Edges, e_ranks)
        if np.all(ind < len(Edges)) and np.all(Edges[ind] == e_ranks):
          Triangles.extend(array('I', T))
  result = {
    'vertices' : Vertices, 
    'edges' : np.array([unrank_C2(x,N) for x in Edges], dtype=int).reshape((len(Edges), 2)),
    'triangles' : np.asarray(Triangles).reshape((int(len(Triangles)/3), 3))
  }
  return(result)




def low_entry(j: int, D: csc_matrix):
  """ Provides O(1) access to low entries of D """
  assert isinstance(D, csc_matrix)
  nnz_j = np.abs(D.indptr[j+1]-D.indptr[j]) 
  return(D.indices[D.indptr[j]+nnz_j-1] if nnz_j > 0 else -1)

def reduction(D1: csc_matrix, D2: csc_matrix):
  assert isinstance(D1, csc_matrix) and isinstance(D2, csc_matrix), 
  assert D1.shape[1] == D2.shape[0], "Must be matching boundary matrices"
  n, m, k = D1.shape[0], D2.shape[0], D2.shape[1]
  V1, V2 = sps.identity(m), sps.identity(k)

  piv1 = np.array([low_entry(j, D1) for j in range(m)], dtype=int)
  piv2 = np.array([low_entry(j, D2) for j in range(k)], dtype=int)

  ## Reduce D1
  for j in range(1, m):
    while( piv1[j] != -1 and np.any(J := piv1[:j] == piv1[j]) ):
      jj = np.flatnonzero(J)[0] # guarenteed to exist
      
      raise ValueError("test")

  ## Reduce D2

# class Reduction():
#   def __init__(D0: csc_matrix, D1: csc_matrix): # boundary matrix
    

