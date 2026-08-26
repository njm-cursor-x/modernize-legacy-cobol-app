# Legacy COBOL account system

Archived GnuCOBOL sources. Behavior is unchanged from the original program.

## Compile and run

```bash
cobc -x main.cob operations.cob data.cob -o accountsystem
./accountsystem
```

GnuCOBOL (`cobc`) is required. Opening balance is 1000.00 (in-memory; not persisted across process restarts).
