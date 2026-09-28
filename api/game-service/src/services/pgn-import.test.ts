jest.mock("../config/redis");

import { GameService } from "./game.service";
import { ChessEngine } from "./chess-engine";

const MATE_PGN = [
  '[Event "Quick"]',
  '[White "Alice"]',
  '[Black "Bob"]',
  '[Result "1-0"]',
  '[TimeControl "600+5"]',
  "",
  "1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0",
].join("\n");

describe("GameService.importGame helpers", () => {
  describe("_parseTimeControl", () => {
    it("parses initial + increment", () => {
      expect(GameService._parseTimeControl("600+5")).toEqual({ initial: 600, increment: 5 });
    });

    it("parses initial only", () => {
      expect(GameService._parseTimeControl("300")).toEqual({ initial: 300, increment: 0 });
    });

    it("falls back to rapid for empty input", () => {
      expect(GameService._parseTimeControl()).toEqual({ initial: 600, increment: 5 });
    });

    it("falls back to rapid for junk input", () => {
      expect(GameService._parseTimeControl("not-a-clock")).toEqual({ initial: 600, increment: 5 });
    });
  });

  describe("_syntheticPlayer", () => {
    it("builds an imported placeholder player", () => {
      const p = GameService._syntheticPlayer("Bob");
      expect(p.username).toBe("Bob");
      expect(p.userId).toBe("imported:bob");
      expect(p.rating).toBe(1200);
    });
  });

  describe("_importMoves", () => {
    it("converts PGN moves to IMove records with SAN and per-move FEN", () => {
      const moves = GameService._importMoves(MATE_PGN, 600, 1000000);
      expect(moves).toHaveLength(7);
      expect(moves[0].san).toBe("e4");
      expect(moves[0].from).toBe("e2");
      expect(moves[0].to).toBe("e4");
      expect(moves[0].color).toBe("w");
      expect(moves[0].moveNumber).toBe(1);
      expect(moves[0].fen).toContain("rnbqkbnr");
      expect(moves[6].san).toBe("Qxf7#");
      expect(moves[6].moveNumber).toBe(4);
      expect(moves[6].fen.split(" ")[0]).toBe("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR");
    });

    it("tracks synthetic clocks decreasing from the initial value", () => {
      const moves = GameService._importMoves(MATE_PGN, 600, 1000000);
      expect(moves[0].clock).toBeLessThanOrEqual(600);
      expect(moves[1].clock).toBeLessThan(moves[0].clock);
    });
  });

  describe("_classifyImport", () => {
    const white = { userId: "w-1", username: "Alice", rating: 1200 };
    const black = { userId: "b-1", username: "Bob", rating: 1200 };

    it("classifies a decisive PGN whose final position is checkmate", () => {
      const engine = new ChessEngine();
      engine.loadPgn(MATE_PGN);
      const out = GameService._classifyImport(engine, white, black, "1-0");
      expect(out.result).toBe("WHITE_WIN");
      expect(out.termination).toBe("CHECKMATE");
      expect(out.winner).toBe("w-1");
    });

    it("treats a decisive non-mate position as resignation", () => {
      const engine = new ChessEngine();
      engine.loadPgn('[White "Alice"]\n[Black "Bob"]\n[Result "0-1"]\n\n1. e4 f6 2. d4 Kf7');
      const out = GameService._classifyImport(engine, white, black, "0-1");
      expect(out.result).toBe("BLACK_WIN");
      expect(out.termination).toBe("RESIGNATION");
      expect(out.winner).toBe("b-1");
    });

    it("classifies a draw (threefold repetition)", () => {
      const repetitionPgn =
        '[White "Alice"]\n[Black "Bob"]\n[Result "1/2-1/2"]\n\n' +
        "1. Nf3 Nf6 2. Ng1 Ng8 3. Nf3 Nf6 4. Ng1 Ng8 5. Nf3 Nf6 6. Ng1 Ng8 1/2-1/2";
      const engine = new ChessEngine();
      engine.loadPgn(repetitionPgn);
      const out = GameService._classifyImport(engine, white, black, "1/2-1/2");
      expect(out.result).toBe("DRAW");
      expect(out.termination).toBe("THREEFOLD_REPETITION");
    });

    it("classifies a draw (stalemate)", () => {
      const stalematePgn =
        '[White "Alice"]\n[Black "Bob"]\n[Result "1/2-1/2"]\n\n' +
        "1. e3 a5 2. Qh5 Ra6 3. Qxa5 h5 4. Qxc7 Rah6 5. h4 f6 6. Qxd7+ Kf7 7. Qxb7 Qd3 8. Qxb8 Qh7 9. Qxc8 Kg6 10. Qe6 1/2-1/2";
      const engine = new ChessEngine();
      engine.loadPgn(stalematePgn);
      const out = GameService._classifyImport(engine, white, black, "1/2-1/2");
      expect(out.result).toBe("DRAW");
      expect(out.termination).toBe("STALEMATE");
    });

    it("leaves result null for unfinished PGNs", () => {
      const engine = new ChessEngine();
      engine.loadPgn('[White "Alice"]\n[Black "Bob"]\n[Result "*"]\n\n1. e4 e5');
      const out = GameService._classifyImport(engine, white, black, "*");
      expect(out.result).toBeNull();
    });
  });

  describe("ChessEngine.loadPgn", () => {
    it("throws on invalid PGN", () => {
      const engine = new ChessEngine();
      expect(() => engine.loadPgn("this is not a pgn")).toThrow();
    });

    it("exposes parsed headers", () => {
      const engine = new ChessEngine();
      engine.loadPgn(MATE_PGN);
      const headers = engine.headers();
      expect(headers["White"]).toBe("Alice");
      expect(headers["Black"]).toBe("Bob");
      expect(headers["Result"]).toBe("1-0");
      expect(headers["TimeControl"]).toBe("600+5");
    });

    it("reproduces a normalized PGN including headers", () => {
      const engine = new ChessEngine();
      engine.loadPgn(MATE_PGN);
      const pgn = engine.state.pgn;
      expect(pgn).toContain('[White "Alice"]');
      expect(pgn).toContain("Qxf7#");
    });
  });
});