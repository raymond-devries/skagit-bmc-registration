import sys

from common import wait_for_supabase_deployment

wait_for_supabase_deployment(sys.argv[1], sys.argv[2])
