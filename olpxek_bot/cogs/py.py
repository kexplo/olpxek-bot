import concurrent.futures

from discord.ext import commands

from olpxek_bot.eval_py import eval_py


class PyCog(commands.Cog):
    @commands.command()
    async def py(self, ctx, *, arg):
        with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
            future = pool.submit(eval_py, arg)
            try:
                result = future.result(timeout=1.0)
            except concurrent.futures.TimeoutError:
                print("py TimeoutError")
                for pid, process in pool._processes.items():
                    print(f"kill pid: {pid}")
                    process.kill()
                print("pool.shutdown")
                pool.shutdown(wait=True)
                return await ctx.send("TimeoutError")
            return await ctx.send(result)
